import base64
import json
import math
import threading
import time
from collections import Counter
from urllib.parse import urlsplit

import requests


API_BASE_URL = "https://api.worldquantbrain.com"
PLATFORM_URL = "https://platform.worldquantbrain.com"
AUTH_REFRESH_FALLBACK_SECONDS = 150 * 60
AUTH_REFRESH_SKEW_SECONDS = 5 * 60
AUTH_REFRESH_SECONDS = AUTH_REFRESH_FALLBACK_SECONDS
GET_RETRY_DELAYS = (2.0, 5.0, 10.0)
GET_MIN_INTERVAL_SECONDS = 0.25


class BrainClient:
    """统一请求出口：GET 有界重试，写请求发生传输异常时绝不盲重发。"""

    def __init__(self, session=None):
        self.session = session or requests.Session()
        if session is None:
            self.session.trust_env = False
        self._authenticated_at = None
        self._auth_refresh_at = None
        self._pacing_lock = threading.Lock()
        self._last_get_at = None
        self.request_metrics = Counter()

    @staticmethod
    def _jwt_exp(cookie_value):
        try:
            parts = str(cookie_value).split('.')
            if len(parts) != 3:
                return None
            payload = parts[1] + '=' * (-len(parts[1]) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload.encode('ascii')))
            exp = decoded.get('exp')
            return float(exp) if isinstance(exp, (int, float)) else None
        except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
            return None

    def _session_jwt_exp(self):
        cookies = getattr(self.session, 'cookies', None)
        if cookies is None:
            return None
        try:
            values = [cookie.value for cookie in cookies]
        except TypeError:
            try:
                values = list(cookies.values())
            except (AttributeError, TypeError):
                return None
        expiries = [self._jwt_exp(value) for value in values]
        expiries = [value for value in expiries if value is not None]
        return min(expiries) if expiries else None

    def mark_authenticated(self):
        """按 JWT exp 提前五分钟续签；不可解析时采用150分钟兜底。"""
        now_mono = time.monotonic()
        self._authenticated_at = now_mono
        exp = self._session_jwt_exp()
        delay = AUTH_REFRESH_FALLBACK_SECONDS if exp is None else max(
            0.0, exp - time.time() - AUTH_REFRESH_SKEW_SECONDS
        )
        self._auth_refresh_at = now_mono + delay

    def _refresh_authentication(self) -> bool:
        try:
            response = self.session.request(
                "POST", f"{API_BASE_URL}/authentication", timeout=30
            )
        except requests.exceptions.RequestException as exc:
            print(f"重新登录失败: {type(exc).__name__}")
            return False
        if response.status_code not in (200, 201):
            if response.status_code == 401 and response.headers.get("WWW-Authenticate") == "persona":
                print("重新登录需要人脸认证，请重新执行 login_hk()。")
            else:
                print(f"重新登录失败，状态码: {response.status_code}")
            return False
        self.mark_authenticated()
        print("重新登录成功。")
        return True

    def _pace_get(self):
        with self._pacing_lock:
            now = time.monotonic()
            if self._last_get_at is not None:
                wait = GET_MIN_INTERVAL_SECONDS - (now - self._last_get_at)
                if wait > 0:
                    time.sleep(wait)
            self._last_get_at = time.monotonic()

    @staticmethod
    def _endpoint_label(url):
        path = urlsplit(url).path or '/'
        for prefix, label in (
            ('/simulations', 'simulation'), ('/alphas', 'alpha'),
            ('/authentication', 'authentication'),
        ):
            if path.startswith(prefix):
                return label
        return path.split('/', 2)[1] if '/' in path else 'other'

    def request(self, method, url, **kwargs):
        """GET 有界重试；401仅一次续签；写请求传输异常不重发。"""
        method = str(method).upper()
        url = str(url)
        if not url.startswith(("http://", "https://")):
            url = f"{API_BASE_URL}/{url.lstrip('/')}"
        timeout = kwargs.pop('timeout', 30)
        deadline = kwargs.pop('deadline', None)
        rate_limit_waits = kwargs.pop('rate_limit_waits', None)
        if rate_limit_waits is not None:
            rate_limit_waits = tuple(max(0.0, float(value)) for value in rate_limit_waits)
        is_auth_request = url.rstrip('/') == f"{API_BASE_URL}/authentication"
        reauthenticated = False
        auth_due = (
            self._auth_refresh_at is not None
            and time.monotonic() >= self._auth_refresh_at
        ) or (
            self._auth_refresh_at is None and self._authenticated_at is not None
            and time.monotonic() - self._authenticated_at >= AUTH_REFRESH_FALLBACK_SECONDS
        )
        if not is_auth_request and auth_due:
            reauthenticated = self._refresh_authentication()

        retry_delays = GET_RETRY_DELAYS if (method == 'GET' or is_auth_request) else ()
        attempt = 0
        rate_limit_count = 0
        while True:
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                if isinstance(timeout, (int, float)):
                    timeout = min(timeout, remaining)
            if method == 'GET':
                self._pace_get()
            try:
                response = self.session.request(method, url, timeout=timeout, **kwargs)
            except requests.exceptions.RequestException as exc:
                self.request_metrics['connection_resets' if (
                    getattr(exc, 'winerror', None) == 10054 or '10054' in str(exc)
                ) else 'transport_errors'] += 1
                if attempt >= len(retry_delays):
                    print(
                        f"[{method}] endpoint={self._endpoint_label(url)} "
                        f"error={type(exc).__name__} attempts={attempt + 1} state=PENDING"
                    )
                    return None
                wait = retry_delays[attempt]
                if deadline is not None and wait >= deadline - time.monotonic():
                    return None
                attempt += 1
                print(
                    f"[{method}] endpoint={self._endpoint_label(url)} "
                    f"error={type(exc).__name__} retry={attempt}/{len(retry_delays)} wait={wait:g}s"
                )
                time.sleep(wait)
                continue
            if response.status_code == 401 and not is_auth_request and not reauthenticated:
                self.request_metrics['auth_401'] += 1
                if self._refresh_authentication():
                    reauthenticated = True
                    continue
                return response
            if response.status_code == 429:
                self.request_metrics['http_429'] += 1
                waits = rate_limit_waits if rate_limit_waits is not None else retry_delays
                if rate_limit_count >= len(waits):
                    return response
                default_wait = waits[rate_limit_count]
                try:
                    header_wait = float(response.headers.get(
                        'retry-after', response.headers.get('Retry-After', default_wait)
                    ))
                except (TypeError, ValueError):
                    header_wait = default_wait
                wait = max(default_wait, header_wait)
                if not math.isfinite(wait) or (deadline is not None and wait >= deadline - time.monotonic()):
                    return response
                rate_limit_count += 1
                print(
                    f"[{method}] endpoint={self._endpoint_label(url)} error=HTTP429 "
                    f"retry={rate_limit_count}/{len(waits)} wait={wait:g}s"
                )
                time.sleep(wait)
                continue
            if (method == 'GET' or is_auth_request) and 500 <= response.status_code < 600:
                self.request_metrics['http_5xx'] += 1
                if attempt >= len(retry_delays):
                    return response
                wait = retry_delays[attempt]
                if deadline is not None and wait >= deadline - time.monotonic():
                    return response
                attempt += 1
                print(
                    f"[{method}] endpoint={self._endpoint_label(url)} "
                    f"error=HTTP{response.status_code} retry={attempt}/{len(retry_delays)} "
                    f"wait={wait:g}s"
                )
                time.sleep(wait)
                continue
            return response

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request('PATCH', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def options(self, url, **kwargs):
        return self.request('OPTIONS', url, **kwargs)
