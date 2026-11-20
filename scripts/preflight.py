"""Preflight verification script: runs hero evaluation N times and tests verdict stability."""

import argparse
from pathlib import Path
import sys
import httpx

FIXTURES_DIR = Path("fixtures")
MAIN_BID_PATH = FIXTURES_DIR / "GEM-2026-B-7945477-main-bid.pdf"
CORRIGENDUM_PATH = FIXTURES_DIR / "GEM-2026-B-7945477-C5-corrigendum.pdf"


def run_preflight(base_url: str, runs: int) -> int:
    """Execute preflight test uploading tender and bidders, evaluating N times for stability."""
    base = base_url.rstrip("/")
    client = httpx.Client(timeout=300.0)

    print(f"--- Starting Preflight Verification against {base} ({runs} runs) ---")

    # 1. Upload Tender Documents (Main bid first, then corrigendum)
    if not MAIN_BID_PATH.is_file() or not CORRIGENDUM_PATH.is_file():
        print(f"Error: Fixture PDFs missing in {FIXTURES_DIR}")
        return 1

    tender_files = [
        ("files", (MAIN_BID_PATH.name, MAIN_BID_PATH.read_bytes(), "application/pdf")),
        ("files", (CORRIGENDUM_PATH.name, CORRIGENDUM_PATH.read_bytes(), "application/pdf")),
    ]
    t_resp = client.post(f"{base}/tenders", files=tender_files)
    if t_resp.status_code != 200:
        print(f"Error creating tender: HTTP {t_resp.status_code} - {t_resp.text}")
        return 1

    tender_id = t_resp.json()["tender_id"]
    print(f"Created Tender ID: {tender_id}")

    # 2. Upload the three bidder packs
    bidders = [
        ("PassBidder Pvt Ltd", FIXTURES_DIR / "bidder_pass.pdf"),
        ("FailBidder Pvt Ltd", FIXTURES_DIR / "bidder_fail.pdf"),
        ("ReviewBidder Pvt Ltd", FIXTURES_DIR / "bidder_review.pdf"),
    ]
    for b_name, b_path in bidders:
        b_files = [("files", (b_path.name, b_path.read_bytes(), "application/pdf"))]
        b_resp = client.post(f"{base}/tenders/{tender_id}/bidders", data={"name": b_name}, files=b_files)
        if b_resp.status_code != 200:
            print(f"Error adding bidder '{b_name}': HTTP {b_resp.status_code} - {b_resp.text}")
            return 1
        print(f"Registered bidder: {b_name}")

    # 3. Evaluate N times and check verdict stability
    print(f"\nRunning {runs} consecutive evaluations...")
    baseline_verdicts = None
    passed_runs = 0

    for i in range(1, runs + 1):
        eval_resp = client.post(f"{base}/tenders/{tender_id}/evaluate")
        if eval_resp.status_code != 200:
            print(f"Run {i}: Evaluation failed with HTTP {eval_resp.status_code}")
            continue

        data = eval_resp.json()
        current_verdicts = {
            (r["criterion_id"], r["bidder_name"]): r["verdict"]
            for r in data.get("results", [])
        }
        is_cached = data.get("cached", False)
        is_degraded = data.get("degraded", False)

        if baseline_verdicts is None:
            baseline_verdicts = current_verdicts
            passed_runs += 1
            print(f"Run 1 (Baseline): {len(current_verdicts)} verdicts recorded. Cached={is_cached}, Degraded={is_degraded}")
        else:
            if current_verdicts == baseline_verdicts:
                passed_runs += 1
                print(f"Run {i}: Identical verdicts. Cached={is_cached}, Degraded={is_degraded}")
            else:
                print(f"Run {i}: Verdict mismatch! {current_verdicts} vs baseline {baseline_verdicts}")

    # 4. Final summary output
    print(f"\nPreflight: {passed_runs} of {runs} runs with identical verdicts.")
    return 0 if passed_runs == runs else 1


def main() -> None:
    """Parse CLI arguments and run preflight."""
    parser = argparse.ArgumentParser(description="BidParakh Evaluation Preflight Verification")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL of deployed service")
    parser.add_argument("--runs", type=int, default=10, help="Number of evaluation runs (default: 10)")
    args = parser.parse_args()

    exit_code = run_preflight(args.base_url, args.runs)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
