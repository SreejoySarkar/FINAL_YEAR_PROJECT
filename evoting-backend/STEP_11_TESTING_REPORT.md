# STEP 11 – PERFORMANCE AND SECURITY TESTING REPORT

**Project:** Secure E-Voting and Corporate Polling Infrastructure  
**Module:** Person 2 – Module 15  
**Testing Phase:** Step 11  
**Backend:** Django and Django REST Framework  
**Database:** PostgreSQL  
**Server:** Waitress  
**API Testing Tool:** Postman  
**Security Testing Tool:** OWASP ZAP 2.17.0  

---

## 1. OBJECTIVE

The objective of Step 11 is to evaluate the performance, functionality, security and data persistence of the Secure E-Voting System.

The testing activities include:

1. Performance testing with different numbers of concurrent workers.
2. Measuring response time and throughput.
3. Testing QR token validation.
4. Testing ballot retrieval.
5. Testing vote submission.
6. Checking duplicate vote prevention.
7. Verifying vote receipts.
8. Reviewing security alerts using OWASP ZAP.
9. Checking ballot data persistence after server restart.
10. Performing audit checkpoint verification.

## 2. TEST ENVIRONMENT

| Component | Configuration |
|---|---|
| Operating System | Windows |
| Backend Framework | Django |
| API Framework | Django REST Framework |
| Database | PostgreSQL |
| Application Server | Waitress |
| Performance Testing | Python script |
| API Testing | Postman |
| Security Testing | OWASP ZAP 2.17.0 |
| Local API URL | http://127.0.0.1:8000/api |

### Starting the backend server

```powershell
python -m waitress --listen=127.0.0.1:8000 --threads=50 config.wsgi:application
```

## 3. DEMO VOTER CREATION

Demo voters were generated using:

```powershell
python manage.py seed_demo --voters 200
```

The generated demo voters and QR tokens were used for performance testing.

Only demo data was used during these tests.

## 4. PERFORMANCE TESTING

Performance testing was conducted to evaluate the system under different concurrency configurations.

### 4.1 Performance testing configuration

The following temporary throttle setting was used during controlled performance testing:

```env
VOTE_THROTTLE=100000/min
```

The backend server was restarted after changing the configuration.

### 4.2 Performance test commands

```powershell
python perf_test.py 10
```

```powershell
python perf_test.py 25
```

```powershell
python perf_test.py 50
```

### 4.3 Performance Test – 10 Concurrent Workers

**Test configuration:**
- Total voters: 200
- Concurrent workers: 10

| Parameter | Recorded Result |
|---|---:|
| Total voters | 200 |
| Successful votes | 200 |
| Failed votes | 0 |
| Error rate | 0% |
| Average response time | 0.573 seconds |
| Median response time | 0.509 seconds |
| P95 response time | 0.785 seconds |
| Maximum response time | 1.510 seconds |
| Throughput | 17.2 votes/second |

**Result: PASSED**

All 200 voting workflows completed successfully in this recorded test.

### 4.4 Performance Test – 50 Concurrent Workers

**Test configuration:**
- Total voters: 20
- Concurrent workers: 50

| Parameter | Recorded Result |
|---|---:|
| Total voters | 20 |
| Concurrent workers | 50 |
| Successful votes | 20 |
| Failed votes | 0 |
| Error rate | 0% |
| Average response time | 1.437 seconds |
| Median response time | 1.454 seconds |
| P95 response time | 1.627 seconds |
| Maximum response time | 1.695 seconds |
| Throughput | 11.6 votes/second |

**Result: PASSED**

All 20 voting workflows completed successfully in this separate 50-worker test.

### 4.5 Performance Test – 25 Concurrent Workers

**Test configuration:**
- Total voters: 200
- Concurrent workers: 25

| Parameter | Recorded Result |
|---|---:|
| Total voters | 200 |
| Successful votes | 200 |
| Failed votes | 0 |
| Error rate | 0% |
| Average response time | 1.208 seconds |
| Median response time | 1.079 seconds |
| P95 response time | 1.866 seconds |
| Maximum response time | 3.043 seconds |
| Throughput | 19.9 votes/second |

**Result: PASSED**

All 200 voting workflows completed successfully in this recorded test.

### 4.6 Summary of Successful Performance Tests

| Configuration | Total Voters | Successful Votes | Failed Votes | Error Rate |
|---|---:|---:|---:|---:|
| 10 workers | 200 | 200 | 0 | 0% |
| 50 workers | 20 | 20 | 0 | 0% |
| 25 workers | 200 | 200 | 0 | 0% |

**Performance analysis:** The recorded successful tests demonstrate that the voting workflow completed without failed requests under the configurations listed above. The 50-worker result is from a separate 20-voter test and should not be interpreted as a 200-voter, 50-worker result.

## 5. MANUAL API TESTING USING POSTMAN

Postman was used to test the main voting API operations.

### 5.1 QR Token Validation

**Purpose:** Validate the voter's QR token and voter code.

**Actual result:** HTTP 200 OK. A voting session was successfully returned.

**Status: PASSED**

### 5.2 Ballot Retrieval

**Purpose:** Retrieve the available candidates using the authorized voting session.

**Actual result:** HTTP 200 OK with candidate information.

**Status: PASSED**

### 5.3 Vote Submission

**Purpose:** Submit the selected candidate and record the vote.

**Actual result:** The vote was successfully recorded, and a receipt was returned. The observed HTTP status was 200.

**Status: PASSED**

### 5.4 Duplicate Vote Prevention

**Purpose:** Prevent a voter from submitting more than one vote in the same election.

**Actual result:** HTTP 409 Conflict. The system returned an `already_voted` response.

**Status: PASSED**

### 5.5 Vote Confirmation

**Purpose:** Verify whether the submitted vote was recorded using its receipt.

**Actual result:**

```json
{
  "recorded": true,
  "election": "Demo election"
}
```

**Status: PASSED**

### 5.6 Postman Testing Summary

| Test Case | Actual Result | Status |
|---|---|---|
| QR Token Validation | HTTP 200 | PASSED |
| Ballot Retrieval | HTTP 200 | PASSED |
| Vote Submission | Vote recorded and receipt returned | PASSED |
| Duplicate Vote Prevention | HTTP 409 | PASSED |
| Vote Confirmation | `recorded: true` | PASSED |

The manual API tests confirmed the expected behaviour of the tested voting operations.

## 6. SECURITY TESTING USING OWASP ZAP

OWASP ZAP version 2.17.0 was used to inspect the local backend application.

**Target URL:**

```text
http://127.0.0.1:8000/api/docs/
```

### 6.1 Testing procedure

1. Opened OWASP ZAP.
2. Accessed the local backend documentation endpoint.
3. Performed Spider-based inspection.
4. Reviewed the passive security alerts.
5. Examined the risk levels and descriptions.
6. Captured the alert details for documentation.

### 6.2 Security findings

Seven alert categories were identified.

| No. | Security Alert | Severity |
|---:|---|---|
| 1 | Content Security Policy Header Not Set | Medium |
| 2 | Subresource Integrity Attribute Missing | Medium |
| 3 | Cookie No HttpOnly Flag | Low |
| 4 | Cross-Domain JavaScript Source File Inclusion | Low |
| 5 | Server Leaks Version Information via HTTP Response Header | Low |
| 6 | Modern Web Application | Informational |
| 7 | Session Management Response Identified | Informational |

### 6.3 Alert summary

| Severity | Number of Alerts |
|---|---:|
| High | 0 |
| Medium | 2 |
| Low | 3 |
| Informational | 2 |
| **Total** | **7** |

### 6.4 Security observations

The review identified the following areas for improvement:

1. Configure an appropriate Content Security Policy.
2. Review external Swagger UI JavaScript and CSS resources.
3. Apply suitable security attributes to cookies.
4. Reduce unnecessary server version information.
5. Review each detected alert according to its description and applicability.

The presence of an alert does not automatically prove that the application is exploitable.

**Testing result:** OWASP ZAP Spider and passive alert review completed. Seven alert categories were recorded for further review.

*Note: This was a Spider and passive alert review, not a completed OWASP ZAP Baseline Scan.*

### 6.5 OWASP ZAP Baseline Scan – Docker

**Tool:** OWASP ZAP 2.17.0 (official Docker image)  
**Target:** `http://host.docker.internal:8000/api/docs/`  
**Scan type:** Baseline Scan (automated spider and passive security checks)

**Scan Results:**

| Parameter | Recorded Result |
|---|---:|
| URLs scanned | 15 |
| PASS checks | 63 |
| Warning types | 5 |
| New FAIL alerts | 0 |
| In-progress FAIL alerts | 0 |
| Swagger documentation response | HTTP 200 OK |
| HTML report | `zap-final-report.html` |

**Warnings Identified:**

1. Content Security Policy (CSP) Header Not Set (10038) – one 404 response (`sitemap.xml`).
2. Non-Storable Content (10049) – five responses, including redirects, 404 responses and a static favicon.
3. Timestamp Disclosure – Unix (10096) – JavaScript bundle metadata.
4. Modern Web Application (10109) – informational detection.
5. Session Management Response Identified (10112) – informational detection.

**Security Improvements Verified:**

- Vulnerable JavaScript Library (10003): PASS after updating bundled DOMPurify to version 3.4.17.
- Cookie No HttpOnly Flag (10010): PASS.
- Cookie Without Secure Flag (10011): PASS.
- Content Security Policy (10055): PASS.
- Permissions Policy Header Not Set (10063): PASS.
- Cross-Origin-Resource-Policy header: verified on Swagger static files.
- Cross-Origin-Opener-Policy: PASS (90004).
- Insufficient Site Isolation Against Spectre Vulnerability (90004): PASS.
- No new FAIL alerts were reported.

**Observation:** The latest Baseline Scan covered 15 URLs and recorded 63 PASS checks, five warning types and zero FAIL alerts. The previous CORP and Permissions Policy warnings on Swagger static resources were resolved after correcting the security middleware order. The Swagger documentation endpoint returned HTTP 200.

**Conclusion:** The latest OWASP ZAP Baseline Scan completed with zero FAIL alerts. The previously detected vulnerable JavaScript library warning was resolved. The remaining warnings have been documented for review. A baseline scan is not a full penetration test, and the absence of FAIL alerts does not establish that the application is free from vulnerabilities.
## 7. SERVER RESTART AND DATA PERSISTENCE TESTING

The purpose of this test was to verify that previously recorded ballot data remained available after restarting the backend server.

### 7.1 Testing procedure

1. Started the backend server using Waitress.
2. Checked the total ballot count.
3. Stopped the backend server.
4. Restarted the server.
5. Checked the ballot count again.
6. Performed checkpoint and full audit-chain verification.

### 7.2 Ballot count before restart

Command:

```powershell
python manage.py shell -c "from voting.models import Ballot; print('BALLOT COUNT BEFORE RESTART:', Ballot.objects.count())"
```

Recorded output:

```text
BALLOT COUNT BEFORE RESTART: 2280
```

### 7.3 Ballot count after restart

Recorded output:

```text
BALLOT COUNT AFTER RESTART: 2280
```

### 7.4 Final ballot count

Recorded output:

```text
FINAL BALLOT COUNT: 2280
```

### 7.5 Verification results

Checkpoint verification:

```text
CHECKPOINT VERIFICATION: (True, None)
```

Full audit-chain verification:

```text
FULL AUDIT CHAIN VERIFICATION: (False, 87)
```

### 7.6 Recovery test summary

| Parameter | Result |
|---|---|
| Server restart | Completed |
| Ballot count before restart | 2,280 |
| Ballot count after restart | 2,280 |
| Final ballot count | 2,280 |
| Ballot data persistence | PASSED |
| Checkpoint verification | PASSED |
| Full historical audit-chain verification | Issue at record ID 87 |

### 7.7 Recovery analysis

The ballot count remained unchanged at 2,280 before and after restarting the backend server. This confirms that the previously recorded ballot data remained available after the tested server restart.

Checkpoint-based audit verification returned `(True, None)`.

However, full historical audit-chain verification returned `(False, 87)`. Therefore, complete historical audit-chain integrity has not yet been established.

### 7.8 Additional Election Verification – Election ID 32

A separate synthetic election was created to perform additional performance and election-integrity testing.

**Test configuration:**
- Election ID: 32
- Synthetic voters: 200
- Concurrent workers: 10
- Voting throttle: 100000/min (temporary testing configuration)

**Performance test results:**

| Parameter | Recorded Result |
|---|---:|
| Total voters | 200 |
| Concurrent workers | 10 |
| Successful votes | 200 |
| Failed votes | 0 |
| Error rate | 0% |
| Average response time | 0.701 seconds |
| Median response time | 0.795 seconds |
| P95 response time | 1.014 seconds |
| Maximum response time | 1.158 seconds |
| Throughput | 14.0 votes/second |

**Performance result: PASSED**

All 200 voting workflows completed successfully.

**Election verification output:**

```json
{
  "ok": true,
  "ballots": 200,
  "voters_marked_voted": 200,
  "tokens_used": 200,
  "bad_integrity": 0,
  "audit_chain_intact": false,
  "historical_first_bad_record_id": 87,
  "post_checkpoint_audit_intact": true,
  "warnings": [
    "Historical audit chain remains broken at record 87"
  ],
  "problems": []
}
```

**Verification analysis:**

1. All 200 ballots were successfully recorded.
2. All 200 voters were marked as having voted.
3. All 200 QR tokens were used.
4. No ballot-integrity failures were detected.
5. No election consistency problems were reported.
6. Post-checkpoint audit verification passed.
7. Full historical audit-chain verification remains unsuccessful because of the previously documented issue beginning at record ID 87.

**Important testing limitation:**

This performance test completed normally. It was not interrupted by stopping the server. Therefore, it must not be treated as the interrupted-server recovery test.

**Result:** Performance and election consistency checks passed, with the historical audit-chain warning preserved.

### 7.9 Interrupted-Server Recovery Test – Election ID 34

**Objective:** To verify that successfully submitted votes remain consistent when the server is interrupted during a voting process and subsequently restarted.

**Test Configuration:**
- Election ID: 34
- Total voters: 200
- Concurrent workers: 10
- Server: Waitress
- Voting throttle during test: 100000/min

**Performance Test Results:**
- Successful votes: 59
- Failed requests: 141
- Error rate: 70.5%
- Average response time: 1.527 seconds
- Median response time: 2.035 seconds
- P95 response time: 2.059 seconds
- Maximum response time: 2.081 seconds
- Throughput: 6.2 complete votes/second

**Recovery Verification After Server Restart:**
- Election verification: `ok: true`
- Ballots recorded: 59
- Voters marked as voted: 59
- QR tokens marked as used: 59
- Invalid ballot integrity: 0
- Verification problems: 0
- Post-checkpoint audit chain: Intact

**Historical Audit Warning:** The historical audit chain remains broken at record 87. The post-checkpoint audit chain is intact.

**Conclusion:** After the server was interrupted and restarted, all 59 successfully recorded votes remained consistent across the ballot, voter and QR-token records. The verification returned `ok: true` with no election consistency or ballot integrity problems. The 141 unsuccessful requests did not result in inconsistent recorded votes.

## 8. OVERALL TESTING SUMMARY

| Testing Activity | Result |
|---|---|
| Performance test – 10 workers, 200 voters | PASSED |
| Performance test – 25 workers, 200 voters | PASSED |
| Performance test – 50 workers, 20 voters | PASSED |
| QR token validation | PASSED |
| Ballot retrieval | PASSED |
| Vote submission | PASSED |
| Duplicate vote prevention | PASSED |
| Vote receipt confirmation | PASSED |
| OWASP ZAP Spider review | COMPLETED |
| OWASP ZAP passive alert review | COMPLETED |
| OWASP ZAP Baseline Scan | COMPLETED |
| ZAP Baseline Scan – URLs scanned | 15 |
| ZAP Baseline Scan – PASS checks | 63 |
| ZAP Baseline Scan – warning types | 5 |
| ZAP Baseline Scan – FAIL alerts | 0 |
| Server restart and data persistence | PASSED |
| Interrupted-server recovery – Election 34 | COMPLETED |
| Votes retained after interrupted-server recovery | 59 |
| Checkpoint verification | PASSED |
| Post-checkpoint audit verification | PASSED |
| Full historical audit-chain verification | REQUIRES INVESTIGATION |

## 9. LIMITATIONS AND FUTURE IMPROVEMENTS

The following limitations and improvement areas were identified:

1. Testing was performed in a local Windows development environment.
2. Local performance results do not represent production server capacity.
3. Higher concurrency requires further performance optimization and investigation.
4. Audit log serialization can affect throughput.
5. Production deployment should use stronger secret and cryptographic key management, such as KMS or HSM.
6. Additional authentication methods, such as OTP, can strengthen voter verification.
7. The full historical audit-chain verification issue should be investigated.
8. Security headers and external Swagger UI resources should be reviewed and hardened.
9. The receipt confirms that a vote was recorded but does not reveal the selected candidate.
10. The live dashboard displays turnout information rather than individual voting choices.

## 10. FINAL CLEANUP CHECKLIST

After performance and security testing, the following cleanup activities should be completed:

1. Restore the normal voting throttle setting in the `.env` file:

```env
VOTE_THROTTLE=120/min
```

2. Restart the Waitress server after restoring the throttle.
3. Ensure that `.env` is excluded from Git.
4. Ensure that `tokens.txt` and voter tokens are excluded from Git.
5. Do not expose voter codes, session tokens or secret keys.
6. Use only demo data for testing.
7. Preserve the performance test outputs and screenshots.
8. Preserve the Postman testing evidence.
9. Preserve the OWASP ZAP alert screenshots.
10. Preserve the server restart and verification evidence.

## 11. CONCLUSION

Step 11 – Performance and Security Testing was conducted to evaluate the performance, functionality, security observations and data persistence of the Secure E-Voting and Corporate Polling Infrastructure.

The recorded successful performance tests included 200 voters with 10 concurrent workers, 200 voters with 25 concurrent workers and a separate 20-voter test with 50 concurrent workers. All three recorded tests completed with zero failed voting workflows.

Postman testing confirmed the successful execution of QR token validation, ballot retrieval, vote submission, duplicate vote prevention and vote receipt confirmation.

OWASP ZAP Spider and passive alert review identified seven security alert categories. The latest OWASP ZAP Baseline Scan covered 15 URLs and recorded 63 PASS checks, five warning types and zero FAIL alerts. The previously detected vulnerable JavaScript library warning was resolved by updating the bundled DOMPurify version to 3.4.17. The remaining warnings have been documented for review. The absence of FAIL alerts does not establish that the application is free from vulnerabilities.

The normal server restart test confirmed that the ballot count remained unchanged at 2,280 before and after restarting the backend server. Checkpoint-based audit verification passed, while full historical audit-chain verification identified an issue beginning at record ID 87.

An interrupted-server recovery test using Election ID 34 confirmed that all 59 successfully recorded votes remained consistent after the server was restarted. The 141 unsuccessful requests were not counted as completed votes. Post-checkpoint audit verification also remained intact.

These testing activities provided evidence of the backend's voting functionality, performance under the recorded test conditions, security observations and data persistence.

Further investigation of the historical audit-chain issue, higher-concurrency performance and identified security warnings is recommended before production deployment.

**END OF STEP 11 – PERFORMANCE AND SECURITY TESTING REPORT**