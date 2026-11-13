from rest_framework.test import APIClient


def validate(token, voter_code):
    return APIClient().post(
        "/api/qr/validate",
        {"token": token, "voter_code": voter_code},
        format="json"
    )


def session_for(live):
    r = validate(live["token"], live["voter"].voter_code)
    assert r.status_code == 200
    return r.data["vote_session"]


def vote(session, candidate_id):
    return APIClient().post(
        "/api/votes/submit",
        {"candidate_id": candidate_id},
        format="json",
        HTTP_X_VOTE_SESSION=session
    )