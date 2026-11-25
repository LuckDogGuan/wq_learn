import argparse, json, time, sys
from datetime import datetime
from pathlib import Path
import yaml, requests

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = PROJECT_ROOT / "Password" / "config.yaml"
CHECKPOINT_FILE = PROJECT_ROOT / "result" / "ra_checkpoint.json"
LOG_FILE = PROJECT_ROOT / "result" / "ra_resim.log"
API = "https://api.worldquantbrain.com"
TERMINAL_STATES = {"COMPLETE", "ERROR", "FAIL", "CANCELLED"}
UNRECOVERABLE_ERRORS = {"Region agnostic simulations must have more than one regions"}


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def authenticate(username, password):
    import base64
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    log(f"Logging in: {username}")
    # BRAIN uses Basic Auth (base64-encoded email:password)
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    r = session.post(
        f"{API}/authentication",
        headers={"Authorization": f"Basic {encoded}"},
    )
    r.raise_for_status()
    log(f"Login OK (status={r.status_code})")
    return session


def get_os_regular_alphas(session):
    alphas, offset = [], 0
    log("Fetching OS Regular Alpha list...")
    while True:
        r = session.get(
            f"{API}/users/self/alphas",
            params={"stage": "OS", "limit": 100, "offset": offset, "order": "dateSubmitted"},
        )
        r.raise_for_status()
        page = r.json().get("results", [])
        regular_page = [a for a in page if a.get("type") == "REGULAR"]
        alphas.extend(regular_page)
        log(f"  offset={offset}: page={len(page)}, REGULAR={len(regular_page)}, total={len(alphas)}")
        if len(page) < 100:
            break
        offset += len(page)
    log(f"Total OS REGULAR Alpha: {len(alphas)}")
    return alphas


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint):
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def checkpoint_key(alpha_id, universe):
    return f"{alpha_id}::{universe}"


def is_terminal(entry):
    status = entry.get("status", "")
    return status in TERMINAL_STATES or status == "POST_ERROR_UNRECOVERABLE"


def build_payload(expression, universe, decay=10, neutralization="STATISTICAL"):
    return {
        "type": "REGION_AGNOSTIC",
        "settings": {
            "instrumentType": "EQUITY",
            "region": "ALL",
            "universe": universe,
            "delay": 1,
            "decay": decay,
            "neutralization": neutralization,
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "language": "FASTEXPR",
            "visualization": False,
        },
        "regular": expression,
    }


def create_ra_simulation(session, expression, universe):
    payload = build_payload(expression, universe)
    for attempt in range(20):
        try:
            r = session.post(f"{API}/simulations", json=payload, timeout=60)
            if r.status_code == 429 or "CONCURRENT_SIMULATION_LIMIT_EXCEEDED" in r.text:
                retry_after = float(r.headers.get("Retry-After", "30"))
                log(f"    Rate limited, wait {retry_after}s (attempt {attempt+1}/20)...", "WARN")
                time.sleep(retry_after)
                continue
            if r.status_code == 201:
                return r.headers.get("Location", ""), None
            resp_text = r.text
            is_unrecoverable = any(kw in resp_text for kw in UNRECOVERABLE_ERRORS)
            error_entry = {
                "status": "POST_ERROR_UNRECOVERABLE" if is_unrecoverable else "POST_ERROR_TEMP",
                "http_status": r.status_code,
                "response": resp_text[:500],
                "timestamp": datetime.now().isoformat(),
            }
            if is_unrecoverable:
                log(f"    Unrecoverable error: {resp_text[:200]}", "WARN")
                return None, error_entry
            log(f"    Temp error HTTP {r.status_code}, wait 30s...", "WARN")
            time.sleep(30)
        except Exception as e:
            log(f"    Network error: {e}, wait 10s...", "WARN")
            time.sleep(10)
    return None, {
        "status": "POST_ERROR_UNRECOVERABLE",
        "response": "Max retries exceeded",
        "timestamp": datetime.now().isoformat(),
    }


def fetch_alpha_metrics(session, alpha_id):
    """Fetch sharpe/fitness/turnover for a completed RA alpha."""
    try:
        r = session.get(f"{API}/alphas/{alpha_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            is_data = data.get("is") or {}
            return {
                "sharpe": is_data.get("sharpe"),
                "fitness": is_data.get("fitness"),
                "turnover": is_data.get("turnover"),
                "ra_alpha_id": alpha_id,
            }
    except Exception as e:
        log(f"    fetch_alpha_metrics error: {e}", "WARN")
    return {"sharpe": None, "fitness": None, "turnover": None, "ra_alpha_id": alpha_id}


def poll_simulation(session, location, poll_interval=10, timeout=600):
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            return {"status": "TIMEOUT", "location": location}
        try:
            r = session.get(location, timeout=30)
            if r.status_code == 200:
                data = r.json()
                status = data.get("status") or "QUEUED"
                if status in TERMINAL_STATES:
                    # RA COMPLETE: also fetch alpha metrics
                    if status == "COMPLETE" and data.get("alpha"):
                        metrics = fetch_alpha_metrics(session, data["alpha"])
                        data.update(metrics)
                    return data
                log(f"      Polling status={status} ({int(elapsed)}s)")
        except Exception as e:
            log(f"      Poll error: {e}", "WARN")
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Batch re-simulate OS Regular Alphas as Region-Agnostic"
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually run simulations (default: inventory only)"
    )
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument(
        "--universe", nargs="+", default=["LARGE"],
        choices=["LARGE", "MEDIUM", "SMALL"]
    )
    parser.add_argument("--poll-timeout", type=int, default=600)
    parser.add_argument("--no-poll", action="store_true", help="Submit only, skip polling")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "INVENTORY"
    log("=" * 60)
    log(f"RA Batch Resim | mode={mode} | universe={args.universe} | max={args.max_items}")
    log("=" * 60)

    cfg = load_config()
    session = authenticate(cfg["username"], cfg["password"])
    alphas = get_os_regular_alphas(session)

    if not args.execute:
        log(f"\n=== INVENTORY: {len(alphas)} OS Regular Alpha found ===")
        for i, a in enumerate(alphas[:30], 1):
            expr = (a.get("regular") or {}).get("code", "") or ""
            log(f"  [{i:03d}] id={a.get(chr(39) + 'id' + chr(39))} | {expr[:80]}")
        if len(alphas) > 30:
            log(f"  ... {len(alphas)-30} more (add --execute to start resim)")
        return

    checkpoint = load_checkpoint()
    log(f"Checkpoint loaded: {len(checkpoint)} records")

    tasks = []
    for alpha in alphas:
        alpha_id = alpha.get("id", "")
        expression = (alpha.get("regular") or {}).get("code", "")
        if not expression:
            continue
        for universe in args.universe:
            key = checkpoint_key(alpha_id, universe)
            if is_terminal(checkpoint.get(key, {})):
                continue
            tasks.append({
                "alpha_id": alpha_id,
                "expression": expression,
                "universe": universe,
                "key": key,
            })

    log(f"Tasks to run: {len(tasks)}")
    if args.max_items:
        tasks = tasks[: args.max_items]
        log(f"(Limited to {args.max_items} items)")

    success, fail = 0, 0
    for i, task in enumerate(tasks, 1):
        alpha_id = task["alpha_id"]
        expression = task["expression"]
        universe = task["universe"]
        key = task["key"]
        log(f"\n[{i}/{len(tasks)}] {key}")
        log(f"  expr: {expression[:80]}")

        location, error_entry = create_ra_simulation(session, expression, universe)
        if error_entry:
            checkpoint[key] = {
                "alpha_id": alpha_id,
                "universe": universe,
                "expression": expression[:200],
                **error_entry,
            }
            save_checkpoint(checkpoint)
            if error_entry["status"] == "POST_ERROR_UNRECOVERABLE":
                fail += 1
            continue

        log(f"  Submitted OK: {location}")
        checkpoint[key] = {
            "alpha_id": alpha_id,
            "universe": universe,
            "expression": expression[:200],
            "status": "SUBMITTED",
            "location": location,
            "submitted_at": datetime.now().isoformat(),
        }
        save_checkpoint(checkpoint)

        if args.no_poll:
            continue

        log(f"  Polling (timeout={args.poll_timeout}s)...")
        result = poll_simulation(session, location, timeout=args.poll_timeout)
        final_status = result.get("status", "UNKNOWN")
        sharpe = (result.get("is") or {}).get("sharpe")
        fitness = (result.get("is") or {}).get("fitness")
        turnover = (result.get("is") or {}).get("turnover")
        log(f"  Done: {final_status} | sharpe={sharpe} | fitness={fitness} | turnover={turnover}")
        checkpoint[key].update({
            "status": final_status,
            "completed_at": datetime.now().isoformat(),
            "sharpe": sharpe,
            "fitness": fitness,
            "turnover": turnover,
        })
        save_checkpoint(checkpoint)
        if final_status == "COMPLETE":
            success += 1
        else:
            fail += 1

    log("\n" + "=" * 60)
    log(f"Done! COMPLETE={success} FAIL/ERROR={fail} | checkpoint: {CHECKPOINT_FILE}")
    log("=" * 60)


if __name__ == "__main__":
    main()
