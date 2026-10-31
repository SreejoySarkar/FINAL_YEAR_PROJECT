"""Run:  python manage.py seed_demo --voters 50 && python manage.py runserver
        locust -f tests/performance/locustfile.py --host http://127.0.0.1:8000
Each simulated user casts ONE pre-built ballot (server-side verification cost is what we measure),
then retries it (expects 409) and polls read-only endpoints."""
import itertools
import json
from pathlib import Path

from locust import HttpUser, between, task

DATA = json.loads((Path(__file__).parent / "fixtures.json").read_text())
ELECTION = DATA["election_id"]
_next = itertools.count()


class Voter(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        i = next(_next)
        self.entry = DATA["voters"][i % len(DATA["voters"])]
        self.voted = False

    @task(1)
    def cast_then_duplicate(self):
        if not self.voted:
            with self.client.post("/api/votes/submit/", json=self.entry["payload"], name="submit (first)", catch_response=True) as r:
                r.success() if r.status_code in (201, 409) else r.failure(r.text)
            self.voted = True
        else:
            with self.client.post("/api/votes/submit/", json=self.entry["payload"], name="submit (duplicate)", catch_response=True) as r:
                r.success() if r.status_code == 409 else r.failure(f"expected 409, got {r.status_code}")

    @task(3)
    def read_ballot(self):
        self.client.get(f"/api/ballots/{ELECTION}/", name="ballot")

    @task(2)
    def read_ring(self):
        self.client.get(f"/api/anonymous-auth/ring/{ELECTION}/", name="ring")

    @task(1)
    def bad_qr(self):
        with self.client.post("/api/qr/validate/", json={"token": "garbage"}, name="qr invalid", catch_response=True) as r:
            r.success() if r.status_code == 400 else r.failure(str(r.status_code))
