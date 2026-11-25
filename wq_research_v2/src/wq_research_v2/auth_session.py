"""High-availability BRAIN REST session manager.

Complies with experience_profile.md:
- 10-minute background credential refresh thread (AuthRefreshThread)
- 10-second interval NetworkMonitor auto-reconnect thread
- Strictly verify=True, zero hardcoded local proxies, never logs credentials/cookies
- Strictly NO /alphas/{id}/submit write method anywhere in this client
"""
from __future__ import annotations

import base64
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import requests
import yaml
from requests.adapters import HTTPAdapter

from wq_research_v2.config_loader import PASSWORD_CONFIG_PATH, REPO_ROOT

API_BASE_URL = "https://api.worldquantbrain.com"
DEFAULT_REFRESH_INTERVAL_SEC = 600.0
DEFAULT_NETWORK_POLL_SEC = 10.0


class BiometricsRequiredError(RuntimeError):
    """Raised when BRAIN requires interactive persona/biometric verification."""


def discover_credentials(config_path: Optional[Path] = None) -> tuple[str, str]:
    """Load (username, password) from explicit config_path / Password/config.yaml first, then env fallback."""
    candidates: list[Path] = []
    if config_path:
        candidates.append(Path(config_path))
    env_cfg = os.environ.get("WQ_CONFIG_PATH")
    if env_cfg:
        candidates.append(Path(env_cfg))
    candidates.extend([
        PASSWORD_CONFIG_PATH,
        REPO_ROOT / "goal" / "Password" / "config.yaml",
        Path.home() / "secrets" / "platform-brain.json",
    ])

    for path in candidates:
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw) or {}
        if isinstance(data, list) and len(data) >= 2:
            return str(data[0]).strip(), str(data[1]).strip()
        if isinstance(data, dict):
            user = (
                data.get("username")
                or data.get("email")
                or (data.get("brain") or {}).get("username")
                or (data.get("brain") or {}).get("email")
            )
            pwd = (
                data.get("password")
                or (data.get("brain") or {}).get("password")
            )
            if user and pwd:
                return str(user).strip(), str(pwd).strip()

    env_user = os.environ.get("WQ_USERNAME")
    env_pass = os.environ.get("WQ_PASSWORD")
    if env_user and env_pass:
        return env_user.strip(), env_pass.strip()

    raise FileNotFoundError(
        "WorldQuant Credential not found. Provide Password/config.yaml or set WQ_USERNAME/WQ_PASSWORD."
    )


def parse_jwt_expiry(token: str) -> Optional[float]:
    """Decode JWT exp claim without verification to schedule proactive renewal."""
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded = json.loads(base64.urlsafe_b64decode(payload_b64.encode("ascii")).decode("utf-8"))
        exp = decoded.get("exp")
        return float(exp) if isinstance(exp, (int, float)) else None
    except Exception:
        return None


class BrainAuthSession:
    """Thread-safe WorldQuant BRAIN API client with 10m auth refresh & 10s reconnect."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        *,
        base_url: str = API_BASE_URL,
        refresh_interval_sec: float = DEFAULT_REFRESH_INTERVAL_SEC,
        network_poll_sec: float = DEFAULT_NETWORK_POLL_SEC,
        quota_observer: Optional[Callable[[str, requests.Response], None]] = None,
        session_factory: Optional[Callable[[], requests.Session]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.config_path = config_path
        self.refresh_interval_sec = float(refresh_interval_sec)
        self.network_poll_sec = float(network_poll_sec)
        self.quota_observer = quota_observer

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self.network_available = threading.Event()
        self.network_available.set()

        self.paused_needs_biometrics = False
        self.auth_epoch = 0
        self.last_auth_ts = 0.0
        self.jwt_exp_ts: Optional[float] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

        self.session = session_factory() if session_factory else self._build_session()
        self._refresh_thread: Optional[threading.Thread] = None
        self._net_thread: Optional[threading.Thread] = None

    @staticmethod
    def _build_session() -> requests.Session:
        sess = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
        # Never hardcode local proxy; respect explicit env vars only, verify=True always.
        sess.verify = True
        sess.trust_env = True
        return sess

    def authenticate(self, force: bool = False) -> bool:
        with self._lock:
            now = time.time()
            if (
                not force
                and self.auth_epoch > 0
                and (now - self.last_auth_ts) < self.refresh_interval_sec
                and (self.jwt_exp_ts is None or (self.jwt_exp_ts - now) > 300.0)
            ):
                return True

            if self._username is None or self._password is None:
                self._username, self._password = discover_credentials(self.config_path)

            resp = self.session.post(
                f"{self.base_url}/authentication",
                auth=(self._username, self._password),
                timeout=20,
                verify=True,
            )
            if self.quota_observer is not None:
                self.quota_observer("/authentication", resp)

            www_auth = resp.headers.get("WWW-Authenticate", "")
            if resp.status_code == 401 and "persona" in www_auth.lower():
                self.paused_needs_biometrics = True
                raise BiometricsRequiredError(
                    "BRAIN requires interactive biometric/persona confirmation; pausing automated dispatch."
                )

            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Authentication failed with HTTP {resp.status_code}")

            self.paused_needs_biometrics = False
            self.auth_epoch += 1
            self.last_auth_ts = time.time()
            token = self.session.cookies.get("t")
            self.jwt_exp_ts = parse_jwt_expiry(token) if token else None
            self.network_available.set()
            return True

    def start_background_monitors(self) -> None:
        """Start 10m auth refresh thread and 10s network reconnect monitor."""
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            self._refresh_thread = threading.Thread(
                target=self._auth_refresh_loop,
                name="wq_auth_refresh",
                daemon=True,
            )
            self._refresh_thread.start()
        if self._net_thread is None or not self._net_thread.is_alive():
            self._net_thread = threading.Thread(
                target=self._network_monitor_loop,
                name="wq_network_monitor",
                daemon=True,
            )
            self._net_thread.start()

    def stop_background_monitors(self) -> None:
        self._stop_event.set()
        self.network_available.set()
        for t in (self._refresh_thread, self._net_thread):
            if t is not None and t.is_alive():
                t.join(timeout=2.0)

    def _auth_refresh_loop(self) -> None:
        while not self._stop_event.wait(timeout=min(self.refresh_interval_sec, 60.0)):
            if self.paused_needs_biometrics or not self.network_available.is_set():
                continue
            now = time.time()
            need_refresh = (now - self.last_auth_ts) >= self.refresh_interval_sec or (
                self.jwt_exp_ts is not None and (self.jwt_exp_ts - now) < 300.0
            )
            if need_refresh:
                try:
                    self.authenticate(force=True)
                except BiometricsRequiredError:
                    self.paused_needs_biometrics = True
                except requests.RequestException:
                    self.network_available.clear()
                except Exception:
                    pass

    def _network_monitor_loop(self) -> None:
        while not self._stop_event.wait(timeout=self.network_poll_sec):
            if self.network_available.is_set():
                continue
            try:
                resp = self.session.get(f"{self.base_url}/", timeout=8, verify=True)
                if resp.status_code < 600:
                    self.authenticate(force=True)
                    self.network_available.set()
            except BiometricsRequiredError:
                self.paused_needs_biometrics = True
            except Exception:
                pass

    def mark_network_down(self) -> None:
        self.network_available.clear()

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        timeout: float = 30.0,
        allow_reauth: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute an authenticated HTTP request (hard-blocks /submit write endpoint)."""
        clean_ep = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"
        if method.upper() == "POST" and clean_ep.rstrip("/").endswith("/submit"):
            raise PermissionError(
                "Formal Alpha Submission (/alphas/{id}/submit) is permanently prohibited in wq_research_v2."
            )
        if self.paused_needs_biometrics:
            raise BiometricsRequiredError("Session paused pending biometric verification.")

        if not self.network_available.is_set():
            self.network_available.wait(timeout=max(self.network_poll_sec * 3, 30.0))

        self.authenticate(force=False)
        kwargs["verify"] = True
        try:
            resp = self.session.request(method.upper(), clean_ep, timeout=timeout, **kwargs)
        except requests.RequestException:
            self.mark_network_down()
            raise

        if self.quota_observer is not None:
            self.quota_observer(endpoint, resp)

        if resp.status_code == 401 and allow_reauth:
            self.authenticate(force=True)
            resp = self.session.request(method.upper(), clean_ep, timeout=timeout, **kwargs)
            if self.quota_observer is not None:
                self.quota_observer(endpoint, resp)

        return resp

    def get(self, endpoint: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, *, explicit_user_confirmed: bool = False, **kwargs: Any) -> requests.Response:
        if not explicit_user_confirmed:
            raise PermissionError(
                "Remote Rename Application (PATCH) requires explicit_user_confirmed=True."
            )
        return self.request("PATCH", endpoint, **kwargs)

    def close(self) -> None:
        self.stop_background_monitors()
        self.session.close()
