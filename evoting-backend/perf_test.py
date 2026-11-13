import concurrent.futures as cf
import math
import random
import statistics
import sys
import time
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8000/api"


def vote_once(line):
    token, code = line.split(",", maxsplit=1)
    started_at = time.perf_counter()

    try:
        response = requests.post(
            f"{BASE}/qr/validate",
            json={"token": token, "voter_code": code},
            timeout=20,
        )
        if response.status_code != 200:
            print("QR VALIDATION ERROR:", response.status_code, response.text[:300])
            return "validate_fail", time.perf_counter() - started_at

        body = response.json()
        headers = {"X-Vote-Session": body["vote_session"]}
        ballot_response = requests.get(
            f"{BASE}/elections/{body['election']['id']}/ballot",
            headers=headers,
            timeout=20,
        )
        if ballot_response.status_code != 200:
            return "ballot_fail", time.perf_counter() - started_at

        candidates = ballot_response.json().get("candidates", [])
        if not candidates:
            return "ballot_fail", time.perf_counter() - started_at

        candidate_id = random.choice(candidates)["id"]
        vote_response = requests.post(
            f"{BASE}/votes/submit",
            json={"candidate_id": candidate_id},
            headers=headers,
            timeout=20,
        )
        status = "ok" if vote_response.status_code in (200, 201) else "submit_fail"
        return status, time.perf_counter() - started_at
    except requests.RequestException as e:
        print("PERFORMANCE TEST ERROR:", repr(e))
        return "error", time.perf_counter() - started_at


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    if workers < 1:
        raise SystemExit("Worker count must be at least 1.")

    tokens_path = Path(__file__).with_name("tokens.txt")
    with tokens_path.open(encoding="utf-8") as token_file:
        lines = [line.strip() for line in token_file if line.strip()]

    if not lines:
        raise SystemExit(f"No voter tokens found in {tokens_path}.")

    for line_number, line in enumerate(lines, start=1):
        fields = line.split(",", maxsplit=1)
        if len(fields) != 2 or not all(field.strip() for field in fields):
            raise SystemExit(
                f"Invalid token entry on line {line_number} of {tokens_path}."
            )

    started_at = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(vote_once, lines))

    elapsed = time.perf_counter() - started_at
    times = sorted(duration for _, duration in results)
    successful_votes = sum(1 for status, _ in results if status == "ok")
    failed_votes = len(results) - successful_votes

    print("\nFailure breakdown:")
    for status in ("validate_fail", "ballot_fail", "submit_fail", "error"):
        count = sum(1 for result, _ in results if result == status)
        print(f"{status}: {count}")
    p95_index = math.ceil(0.95 * len(times)) - 1

    print(f"Voters: {len(lines)}   Concurrent workers: {workers}")
    print(
        f"Successful votes: {successful_votes}   Failed: {failed_votes}    "
        f"Error rate: {100 * failed_votes / len(results):.1f}%"
    )
    print(
        f"Avg: {statistics.mean(times):.3f}s   "
        f"Median: {statistics.median(times):.3f}s   "
        f"P95: {times[p95_index]:.3f}s   "
        f"Max: {times[-1]:.3f}s"
    )
    print(f"Throughput: {len(results) / elapsed:.1f} complete votes per second")


if __name__ == "__main__":
    main()
