# Secure E-Voting and Corporate Polling Infrastructure

A Django REST Framework and PostgreSQL-based backend for secure election administration, voter authorization, encrypted anonymous ballots, duplicate-vote prevention, audit logging, election verification, tallying and result publication.

> **Important:** This README combines the Person 1 and Person 2 project responsibilities. Confirm exact endpoint paths, environment-variable names and implementation status against the integrated repository before publishing. Do not claim a feature is complete unless it has been implemented and tested.

## Table of Contents

1. Project Overview
2. Project Objectives
3. Work Division
4. Technology Stack
5. System Architecture and Voting Workflow
6. Security and Privacy Design
7. Database Models
8. Prerequisites
9. Installation and Setup
10. Environment Configuration
11. Database Migrations
12. Running the Server
13. API Documentation
14. API Endpoint Reference
15. Authentication and Permissions
16. Complete Voting Workflow
17. Election Verification and Results
18. Audit Logging and Turnout
19. Automated Testing
20. Performance Testing
21. OWASP ZAP Security Testing
22. Demo Data
23. Frontend Integration
24. Git and Secret Management
25. Troubleshooting
26. Known Limitations
27. Final Project Checklist
28. Contributors

---

## 1. Project Overview

The Secure E-Voting and Corporate Polling Infrastructure is a centralized backend application designed to support secure digital elections and organizational polls.

The system separates election administration from the voter-facing voting process. It provides administrator authentication, role-based access, election creation, candidate management, voter registration, eligibility verification, QR-based voter authorization, encrypted ballot storage, duplicate-vote prevention, audit logging, election verification and result publication.

The application is developed using Django, Django REST Framework and PostgreSQL.

The project is divided into two major development responsibilities:

- **Person 1:** Administration, authentication, election management, voter management, QR generation and shared audit infrastructure.
- **Person 2:** QR validation, voter authorization, ballot management, encryption, duplicate-vote prevention, verification, tallying, results and security testing.

Both parts are integrated into a common backend and database.

## 2. Project Objectives

- Provide secure administrator authentication.
- Implement role-based access control.
- Support election creation and management.
- Support candidate registration and management.
- Support voter registration and CSV import.
- Maintain election-specific voter eligibility.
- Generate signed and time-limited QR tokens.
- Validate voter identity and eligibility before voting.
- Issue short-lived voting sessions.
- Prevent duplicate vote submissions.
- Encrypt ballot information before storage.
- Separate voter identity from stored ballot information.
- Maintain tamper-evident audit records.
- Verify election data and ballot integrity.
- Support tallying, recounting and result finalization.
- Control result publication through permissions.
- Provide API documentation for frontend integration.
- Test the application for functionality, performance and security.

## 3. Work Division

### Person 1 — Administration and Election Management

Person 1 is responsible for the foundation and administrative functionality of the system.

Responsibilities include:

- Django project setup.
- Project settings and URL configuration.
- PostgreSQL database connection.
- Administrator account model.
- Administrator roles and permissions.
- Administrator login.
- OTP verification.
- Logout and token refresh.
- Election creation and management.
- Election publishing and closing.
- Candidate management.
- Voter registration and management.
- CSV voter import.
- Election-specific voter eligibility.
- QR-token generation.
- QR image download.
- Shared audit-log model.
- Audit event helper.
- Audit verification foundation.
- API documentation and initial tests.

### Person 2 — Voting, Security and Results

Person 2 is responsible for the voter-facing voting workflow and security-related functionality.

Responsibilities include:

- QR-token validation.
- Voter identity verification.
- Voter eligibility authorization.
- Short-lived signed voting sessions.
- Ballot retrieval.
- Duplicate-vote prevention.
- Atomic vote submission.
- QR-token used-state update.
- AES-256-GCM ballot encryption.
- HKDF-based key derivation.
- Anonymous ballot storage.
- Audit event integration.
- Audit summary.
- Turnout information.
- Election verification.
- Tallying.
- Recounting.
- Result finalization.
- Hold-on-failure functionality.
- Result publication.
- Security testing.
- Performance testing.

### Shared Integration Requirements

- Both parts must use the same Django project and PostgreSQL database.
- The QR generation and validation components must use compatible signing secrets.
- Both parts must use the shared audit infrastructure.
- Duplicate models and migrations must be avoided.
- Ballot storage must remain separate from voter identity.
- The integrated project must use consistent election status rules.
- Secrets must be shared privately and never committed to GitHub.

## 4. Technology Stack

| Component                    | Technology                     |
| ---------------------------- | ------------------------------ |
| Programming Language         | Python                         |
| Backend Framework            | Django                         |
| API Framework                | Django REST Framework          |
| Database                     | PostgreSQL                     |
| Administrator Authentication | JWT, as configured             |
| Voter Authorization          | Signed voting session          |
| Ballot Encryption            | AES-256-GCM                    |
| Key Derivation               | HKDF                           |
| API Documentation            | drf-spectacular / Swagger UI   |
| Automated Testing            | pytest / Django test framework |
| Local Windows Server         | Waitress                       |
| Manual API Testing           | Postman                        |
| Security Testing             | OWASP ZAP                      |
| Version Control              | Git and GitHub                 |

## 5. System Architecture and Voting Workflow

The application follows a centralized backend architecture.

The major workflow is:

1. Administrator logs in.
2. Administrator completes OTP verification.
3. Election administrator creates an election.
4. Candidates are added.
5. Voters are registered or imported.
6. Eligible voters are associated with the election.
7. QR tokens are generated.
8. Election is published.
9. Voter submits QR token and voter code.
10. Backend validates the token and voter.
11. Backend checks election eligibility and status.
12. Backend generates a short-lived voting session.
13. Voter retrieves the ballot.
14. Voter selects a candidate.
15. Backend validates the voting session and candidate.
16. Backend prevents duplicate submissions.
17. Ballot is encrypted and stored.
18. QR authorization and eligibility state are updated consistently.
19. Voter receives a receipt identifier.
20. Election administrator closes the election.
21. Backend performs election verification.
22. Backend performs tallying and recounting.
23. Results are finalized.
24. Authorized users publish the results.

The election status rules must be enforced by the backend. A voter must not be able to vote before the election opens or after it closes.

## 6. Security and Privacy Design

### 6.1 Administrator Authentication

Administrator endpoints require authentication.

The system uses role-based access control to restrict administrative operations.

Expected roles include:

- `org_admin`
- `election_admin`
- `auditor`

The actual permissions must match the project's permission classes and views.

### 6.2 QR Token Validation

The QR validation process should check:

- Token signature.
- Token existence.
- Token expiry.
- Correct election association.
- Voter identity.
- Voter eligibility.
- Whether the token has already been used.
- Whether the election is open.

The QR token lifetime is configured through the project's environment settings. The development configuration has used a 900-second lifetime.

### 6.3 Short-Lived Voting Session

After successful QR validation, the backend issues a signed voting session.

The Person 2 guide specifies a ten-minute session lifetime.

The voter uses the following HTTP header for authorized voting operations:

`X-Vote-Session: <vote_session>`

Voters must not use administrator JWT tokens for the voting process.

### 6.4 Duplicate-Vote Prevention

The system uses database transactions and row-level locking to prevent duplicate submissions.

Vote submission, ballot creation, eligibility update and QR-token used-state update must be handled consistently.

If a transaction fails, the application must not leave a partially completed vote.

### 6.5 Ballot Encryption

The project uses AES-256-GCM encryption for ballot data.

HKDF is used to derive election-specific encryption keys from the configured master secret.

Each encryption operation must use a unique nonce under the corresponding key.

The ballot master key must not be changed after ballots have been encrypted unless a secure migration or re-encryption process is available.

### 6.6 Anonymous Ballot Storage

The ballot is designed to be stored without a direct voter identifier.

The ballot storage model uses encrypted ballot data and associated integrity and receipt information.

The ballot must not contain a voter foreign key, voter code or direct eligibility reference.

The eligibility record tracks whether a voter has voted. The ballot stores the encrypted choice separately.

### 6.7 Audit Security

Audit logs record important system events without recording the selected candidate or creating a direct voter-to-ballot mapping.

The audit hash chain makes unauthorized modifications detectable. It does not make the database impossible to tamper with.

## 7. Database Models

The following entities represent the main data areas of the system. Confirm the exact model names and fields in the integrated repository.

| Model / Entity         | Purpose                                               |
| ---------------------- | ----------------------------------------------------- |
| Admin / User           | Administrator credentials and roles                   |
| Election               | Election details, dates, status and creator           |
| Candidate              | Candidate information associated with an election     |
| Voter                  | Voter identity and contact information                |
| Eligibility            | Election-specific voter eligibility and voting status |
| QRToken                | QR token information, expiry and used state           |
| Ballot                 | Encrypted anonymous ballot                            |
| AuditLog               | Records administrative and system events              |
| AdminOTP               | Administrator OTP verification information            |
| Result / Tally Records | Stores result and tally information, if implemented   |

## 8. Prerequisites

Install the following software:

- Python 3.12 or the version specified by the project.
- PostgreSQL.
- Git.
- Visual Studio Code.
- Postman.
- OWASP ZAP.

Verify Python:

```powershell
python --version
```

Verify PostgreSQL:

```powershell
psql --version
```

Verify Git:

```powershell
git --version
```

## 9. Installation and Setup

### Step 1: Clone the Repository

```powershell
git clone https://github.com/SreejoySarkar/FINAL_YEAR_PROJECT.git
```

### Step 2: Open the Repository

```powershell
cd FINAL_YEAR_PROJECT
```

### Step 3: Enter the Backend Directory

```powershell
cd evoting-backend
```

### Step 4: Create a Virtual Environment

```powershell
python -m venv venv
```

### Step 5: Activate the Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 6: Install Dependencies

If the repository contains `requirements.txt`, execute:

```powershell
pip install -r requirements.txt
```

If the repository uses a different dependency file, follow the instructions provided in that file.

## 10. Environment Configuration

Create a local `.env` file in the location expected by the Django settings.

Use `.env.example` as a reference.

The following configuration reflects the environment variables currently read by `config/settings.py`.

### PostgreSQL Configuration

```env
DEBUG=True
SECRET_KEY=replace_with_a_secure_django_secret
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=evoting
DB_USER=evoting
DB_PASSWORD=replace_with_your_database_password
DB_HOST=localhost
DB_PORT=5432

QR_SIGNING_KEY=replace_with_a_secure_random_secret
BALLOT_MASTER_KEY=replace_with_a_base64_32_byte_key
INTEGRITY_KEY=replace_with_a_secure_random_secret

VOTE_THROTTLE=120/min
```
Use `DEBUG=False` in production (when the project is deployed online) and configure valid allowed hosts and HTTPS.

If `DB_NAME` is not provided, the backend automatically uses SQLite instead of PostgreSQL.

**Important security instructions:**

- Never use example placeholder values in production.
- Never upload `.env` to GitHub.
- Never share private keys, passwords, QR signing keys or ballot encryption keys.
- Keep the QR signing key consistent between token generation and validation.
- Do not change the ballot master key after storing encrypted ballots.
- Use appropriate secure settings when deploying in production.
- Keep private key directories outside version control.

## 11. Database Migrations

Run migrations after configuring the database.

Create migrations when required:

```powershell
python manage.py makemigrations
```

Apply migrations:

```powershell
python manage.py migrate
```

Check migration status:

```powershell
python manage.py showmigrations
```

Create a Django superuser if required:

```powershell
python manage.py createsuperuser
```

Use the project's custom administrator creation process if it uses a separate administrator model or management command.

## 12. Running the Server

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Start the Django development server:

```powershell
python manage.py runserver
```

For local Windows execution using Waitress:

```powershell
python -m waitress --listen=127.0.0.1:8000 --threads=50 config.wsgi:application
```

The local application is available at:

`http://127.0.0.1:8000/`

Stop the server using `Ctrl + C`.

## 13. API Documentation

The project provides API documentation for developers and frontend integration.

Swagger UI:

`http://127.0.0.1:8000/api/docs/`

API Schema:

`http://127.0.0.1:8000/api/schema/`

Swagger can be used to:

- View available API endpoints.
- Check HTTP methods.
- View required request fields.
- Understand request and response formats.
- Test API endpoints.
- Check authentication requirements.
- Verify exact endpoint paths before frontend integration.

The live Swagger documentation is the source of truth for actual endpoint paths.

## 14. API Endpoint Reference

The following table describes the expected API functionality. Verify the actual URLs and methods in Swagger before using them in the frontend.

### Administrator Authentication

| Functionality    | Description                    |
| ---------------- | ------------------------------ |
| Admin Login      | Authenticates an administrator |
| OTP Verification | Verifies the administrator OTP |
| Token Refresh    | Generates a new access token   |
| Admin Logout     | Ends the administrator session |

### Election Management

| Functionality     | Description                                                   |
| ----------------- | ------------------------------------------------------------- |
| Create Election   | Creates a new election                                        |
| List Elections    | Displays available elections                                  |
| Retrieve Election | Displays election details                                     |
| Update Election   | Updates election information                                  |
| Publish Election  | Makes an election available according to its configured rules |
| Close Election    | Stops further voting                                          |

### Candidate Management

| Functionality    | Description                        |
| ---------------- | ---------------------------------- |
| Add Candidate    | Adds a candidate to an election    |
| List Candidates  | Displays candidates                |
| Update Candidate | Updates candidate information      |
| Delete Candidate | Removes a candidate when permitted |

### Voter Management

| Functionality          | Description                           |
| ---------------------- | ------------------------------------- |
| Add Voter              | Registers a voter                     |
| List Voters            | Displays registered voters            |
| Update Voter           | Updates voter information             |
| CSV Import             | Imports multiple voters               |
| Eligibility Management | Marks voters eligible for an election |

### QR Management

| Functionality     | Description                                |
| ----------------- | ------------------------------------------ |
| Generate QR Token | Generates a QR token for an eligible voter |
| Download QR Image | Provides the QR image                      |
| Validate QR Token | Validates the QR token and voter identity  |

### Voting

| Functionality   | Description                                    |
| --------------- | ---------------------------------------------- |
| Retrieve Ballot | Returns candidates for the authorized election |
| Submit Vote     | Accepts and securely stores a vote             |
| Confirm Receipt | Checks whether a ballot was recorded           |

### Audit and Results

| Functionality         | Description                               |
| --------------------- | ----------------------------------------- |
| Audit Logs            | Displays authorized audit records         |
| Audit Verification    | Checks the audit hash chain               |
| Turnout Summary       | Displays voting participation             |
| Election Verification | Checks election data and ballot integrity |
| Tally                 | Calculates election results               |
| Recount               | Performs a second tally                   |
| Finalization          | Finalizes results after verification      |
| Result Publication    | Makes approved results available          |

**Note:** These are functional descriptions, not guaranteed URL paths. Confirm the actual endpoint paths, HTTP methods, request fields and response formats in Swagger.

## 15. Authentication and Permissions

### 15.1 Administrator Authentication

Administrator endpoints use the authentication method configured in the project.

A typical authenticated request uses:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

The access token is obtained through administrator login and OTP verification.

### 15.2 Administrator Roles

| Role             | General Responsibility            |
| ---------------- | --------------------------------- |
| `org_admin`      | Organization-level administration |
| `election_admin` | Election and voting management    |
| `auditor`        | Audit and verification access     |

Actual permissions must be checked in the project's permission classes and views.

### 15.3 Voter Authentication

Voters do not use administrator JWT credentials.

After successful QR validation, the backend issues a short-lived signed voting session.

The voter sends:

```http
X-Vote-Session: <vote_session>
Content-Type: application/json
```

This session is used for authorized ballot retrieval and vote submission.

## 16. Complete Voting Workflow

### Step 1: Administrator Login

The administrator enters credentials and completes OTP verification.

### Step 2: Create Election

An authorized administrator creates an election with its title, description, start time and end time.

### Step 3: Add Candidates

Candidates are added to the election.

### Step 4: Register Voters

Voters are registered manually or imported through CSV.

### Step 5: Mark Voters Eligible

The required voters are marked eligible for the specific election.

### Step 6: Generate QR Tokens

The backend generates QR tokens for eligible voters.

### Step 7: Publish Election

The election is published according to its configured status and schedule.

### Step 8: Validate QR Token

The voter scans the QR code and provides the required voter code.

The backend checks:

- Token signature.
- Token validity.
- Token expiry.
- Election association.
- Voter identity.
- Voter eligibility.
- Whether the token has already been used.
- Whether the election is open.

### Step 9: Generate Voting Session

If validation succeeds, the backend issues a short-lived signed voting session.

### Step 10: Retrieve Ballot

The voter retrieves the ballot using the `X-Vote-Session` header.

The backend returns the candidates associated with the correct election.

### Step 11: Submit Vote

The voter selects a candidate and submits the vote.

The backend checks the voting session, election status, candidate and eligibility.

### Step 12: Prevent Duplicate Voting

The backend uses database transactions and row-level locking to prevent multiple successful submissions for the same eligibility record.

### Step 13: Encrypt and Store Ballot

The selected vote is encrypted and stored without a direct voter identifier.

### Step 14: Generate Receipt

The backend returns a receipt identifier.

The receipt confirms that the vote was recorded. It does not reveal the candidate selected by the voter.

### Step 15: Close Election

The election is closed after the configured voting period.

### Step 16: Verify and Calculate Results

The backend performs the required verification, tally and recount operations.

### Step 17: Finalize and Publish Results

Results are finalized and published after the required checks and permission checks.

## 17. Election Verification and Results

Election verification checks whether election data and stored ballots satisfy the application's integrity rules.

The verification process may include:

- Checking the election ballot count.
- Checking encrypted ballot integrity.
- Checking receipt uniqueness.
- Checking election-related records.
- Checking audit information.
- Identifying inconsistencies before finalization.

### Tally

The tally process calculates candidate totals after the election is closed.

The application must use the correct election key and decryption process.

### Recount

A recount performs the tally process again to check whether the calculated totals are consistent.

### Finalization

Finalization should be blocked if verification detects unresolved problems.

### Result Publication

Only authorized users should be able to publish results.

Candidate totals should not be exposed to voters while an election is in progress if the project's rules require results to remain hidden.

## 18. Audit Logging and Turnout

### 18.1 Audit Logging

The audit system records important administrative and system events.

Examples include:

- Administrator login.
- OTP verification.
- Election creation.
- Election publication.
- QR validation.
- Vote submission status.
- Election closure.
- Election verification.
- Tally and recount.
- Result finalization.
- Result publication.

Audit records must not contain:

- Selected candidate information.
- Plaintext vote content.
- Direct voter-to-ballot mappings.
- Passwords.
- OTP values.
- Private encryption keys.
- Raw QR secrets.

### 18.2 Audit Hash Chain

The audit system uses a hash-based structure to make unauthorized modifications detectable.

Each event is linked to the previous event according to the implementation.

The verification process checks whether stored records follow the expected chain.

### 18.3 Turnout

The turnout feature provides information about voter participation.

It may display:

- Total eligible voters.
- Total voters who have voted.
- Remaining eligible voters.
- Participation percentage.

Turnout information should be accessible only to authorized users.

Turnout must not reveal the candidate selected by an individual voter.

## 19. Automated Testing

Run the automated tests using the testing framework configured in the repository.

If pytest is configured:

```powershell
pytest
```

If Django's test runner is used:

```powershell
python manage.py test
```

Important testing areas include:

- Administrator login and OTP verification.
- Role-based permissions.
- Election creation and status changes.
- Candidate management.
- Voter registration and CSV import.
- Eligibility validation.
- QR-token generation and validation.
- Expired QR-token rejection.
- Invalid QR-token rejection.
- Voter identity mismatch.
- Unauthorized voter rejection.
- Ballot retrieval.
- Successful vote submission.
- Duplicate-vote prevention.
- Expired voting-session rejection.
- Invalid candidate rejection.
- Ballot encryption and decryption.
- Receipt confirmation.
- Audit-log creation.
- Audit-chain verification.
- Election verification.
- Tally and recount.
- Finalization and result publication.
- Concurrent vote submissions.

Do not report that all tests pass unless the test suite has been executed successfully.

## 20. Performance Testing

Performance testing measures how the voting backend behaves when multiple voters submit requests simultaneously.

The Person 2 guide includes tests using different worker counts:

- 10 workers.
- 25 workers.
- 50 workers.

Record the following for each test:

- Total number of voters.
- Number of successful votes.
- Number of failed votes.
- Failure percentage.
- Average response time.
- Median response time.
- 95th percentile response time.
- Maximum response time.
- Throughput in votes per second.
- Machine and server configuration.

### 20.1 Recorded Development Test Results

The following are actual development test observations, not production benchmarks.

| Workers | Voters | Successful | Failed | Average |  Median |     P95 | Maximum |     Throughput |
| ------- | -----: | ---------: | -----: | ------: | ------: | ------: | ------: | -------------: |
| 10      |    200 |        200 |      0 | 0.573 s | 0.509 s | 0.785 s | 1.510 s | 17.2 votes/sec |
| 25      |    200 |        200 |      0 | 1.208 s | 1.079 s | 1.866 s | 3.043 s | 19.9 votes/sec |
| 50      |     20 |         20 |      0 | 1.437 s | 1.454 s | 1.627 s | 1.695 s | 11.6 votes/sec |

Separate 50-worker tests with 200 voters did not complete successfully in the recorded runs. Failures occurred at different stages, including QR validation, ballot retrieval and vote submission.

Therefore, the 50-worker, 200-voter scenario requires further investigation and must not be reported as a successful test.

### 20.2 Performance Considerations

- Database transactions protect vote consistency.
- Row-level locks prevent duplicate voting.
- Audit-chain writes may be serialized to preserve event ordering.
- Serialized audit writes can limit throughput under heavy concurrent traffic.
- Increasing the number of workers does not always increase throughput.
- Performance depends on the computer, database, server configuration and network.

### 20.3 Throttle Configuration

For controlled local performance testing, the project's rate limit may need temporary adjustment.

Example temporary configuration:

```env
VOTE_THROTTLE=100000/min
```

After testing, restore the normal configured limit:

```env
VOTE_THROTTLE=120/min
```

Restart the server after changing the environment configuration.

Temporary high limits should only be used in a controlled testing environment.

## 21. OWASP ZAP Security Testing

OWASP ZAP is used to identify potential security issues in the web application.

The security review may include HTTP security headers, cookies, external JavaScript resources and other web application behavior.

### 21.1 Security Testing Process

1. Install and open OWASP ZAP.
2. Start the Django backend.
3. Confirm that the application is accessible locally.
4. Configure the target URL.
5. Run the required ZAP Baseline Scan.
6. Review the generated alerts.
7. Check the evidence and affected URLs for each alert.
8. Determine whether each alert applies to the application.
9. Record the findings.
10. Save the generated report for project documentation.

Example local target:

`http://127.0.0.1:8000`

### 21.2 Example Baseline Scan Using Docker

If Docker is installed and running, the following command can be executed from the backend directory:

```powershell
docker run --rm -t -v "${PWD}:/zap/wrk/:rw" ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://host.docker.internal:8000 -r zap-baseline-report.html
```

The report should be generated in the mounted working directory if the scan completes successfully.

### 21.3 Previously Observed Alerts

The following alerts were observed during an earlier Spider/passive review of the local Swagger documentation endpoint:

| Alert                                                            | Severity      |
| ---------------------------------------------------------------- | ------------- |
| Content Security Policy (CSP) Header Not Set                     | Medium        |
| Sub Resource Integrity Attribute Missing                         | Medium        |
| Cookie No HttpOnly Flag                                          | Low           |
| Cross-Domain JavaScript Source File Inclusion                    | Low           |
| Server Leaks Version Information via Server HTTP Response Header | Low           |
| Modern Web Application                                           | Informational |
| Session Management Response Identified                           | Informational |

These findings came from a Spider/passive review of the Swagger documentation endpoint. They must not be described as the completed ZAP Baseline Scan.

An alert does not automatically prove that the application is exploitable. Each finding must be reviewed in context.

## 22. Demo Data

The project includes a demo-data management command for local development.

Check available options:

```powershell
python manage.py seed_demo --help
```

Example commands used during development:

```powershell
python manage.py seed_demo --voters 20
```

```powershell
python manage.py seed_demo --voters 200
```

The demo command may create:

- A demo election.
- Candidate records.
- Voter records.
- Election-specific eligibility records.
- QR tokens for eligible voters.

**Important:** The command may create a new election or overwrite `tokens.txt`. Back up the token file and record the election ID before running it again. Do not repeatedly run a non-idempotent seed command against data that must be preserved.

## 23. Frontend Integration

Frontend developers should use the live Swagger documentation and the API schema as the source of truth.

### 23.1 Administrator Request Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 23.2 Voter Request Headers

```http
X-Vote-Session: <vote_session>
Content-Type: application/json
```

### 23.3 Frontend Responsibilities

- Provide administrator login and OTP screens.
- Provide election management screens.
- Provide candidate management screens.
- Provide voter management screens.
- Support QR scanning and voter-code entry.
- Submit QR token and voter code for validation.
- Use the returned voting session for ballot and submission requests.
- Display candidates for the correct election.
- Handle defined error codes and HTTP statuses.
- Display receipt confirmation without revealing the vote choice.
- Display turnout only to authorized users.
- Display results only after publication and permission checks.

### 23.4 Integration Acceptance Flow

1. Create an election through the administration API.
2. Add at least two candidates.
3. Add synthetic voters.
4. Mark voters eligible.
5. Generate QR tokens and publish the election.
6. Download and scan a QR image.
7. Validate the QR token and voter code.
8. Retrieve the ballot using `X-Vote-Session`.
9. Submit a vote.
10. Confirm that turnout increases.
11. Submit again and confirm that duplicate voting is rejected.
12. Close the election.
13. Run verification, tally, recount, finalization and publication.
14. Confirm that the audit verification endpoint reports an intact chain.

## 24. Git and Secret Management

Never commit the following files or information:

- `.env`
- Private key directories such as `secure_keys/`
- Database dumps containing personal data.
- Real QR tokens.
- `tokens.txt`
- Access and refresh tokens.
- Passwords.
- OTP values.
- Private signing keys.
- Private encryption keys.

The repository should contain an `.env.example` file with fake placeholder values only.

Check Git status:

```powershell
git status --short
```

Check whether sensitive files are ignored:

```powershell
git check-ignore -v .env tokens.txt secure_keys
```

If a secret was committed, adding it to `.gitignore` is not sufficient. Revoke or rotate the secret and remove it from repository history using an approved process.

## 25. Troubleshooting

| Problem                          | Possible Action                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `ModuleNotFoundError`            | Activate the virtual environment and install dependencies.                      |
| PostgreSQL authentication failed | Check database username, password and environment configuration.                |
| Database table does not exist    | Check migration status and apply the required migrations.                       |
| QR token is invalid              | Confirm the signing secret matches between generation and validation.           |
| Ballot key or Base64 error       | Check the key format and required encoding.                                     |
| `InvalidTag` during tally        | Check ciphertext, nonce and whether the master key changed.                     |
| `TransactionManagementError`     | Ensure row-lock operations run inside `transaction.atomic()`.                   |
| HTTP 429                         | The configured rate limit has been reached.                                     |
| CORS error for `X-Vote-Session`  | Add the custom header to the configured CORS allowed headers.                   |
| Results not published (403)      | Check election status and user permissions.                                     |
| Finalization held (409)          | Inspect verification problems, resolve them and run verification again.         |
| 404 or 301 on endpoint           | Check the exact URL and trailing-slash configuration in Swagger.                |
| Migration conflict               | Coordinate migration ownership and reconcile migrations with the shared branch. |

## 26. Known Limitations

The project is an academic prototype. The following limitations should be considered when documenting its security and reliability:

- Ballot anonymity is based on separating voter eligibility from encrypted ballot records. It should not be described as perfect anonymity.
- Someone with full access to both the database and application server may still attempt correlation.
- Keys stored in `.env` are suitable for controlled development, not a substitute for a dedicated key-management service or hardware security module.
- A receipt confirms that a ballot was recorded; it does not prove the content of the vote.
- QR plus voter-code validation is weaker than a separately verified email or phone OTP.
- The live dashboard is designed to show turnout, not candidate counts during voting.
- Recount code in the same application is not a fully independent external audit program.
- Audit-chain ordering may limit throughput if writes are serialized.
- The application should not be described as unhackable or formally certified.
- Only tests actually performed and results actually measured should be reported.

## 27. Final Project Checklist

### Core Voting and Security

- [ ] QR validation checks signature, election, expiry and single-use.
- [ ] Voter authorization checks identity, eligibility and open-election status.
- [ ] Duplicate-vote prevention uses atomic transactions and row locks.
- [ ] Ballot submission works.
- [ ] Ballots contain no voter ID and no timestamp.
- [ ] AES-256-GCM encryption and per-election key derivation work.
- [ ] QR authorization is marked used in the protected transaction.
- [ ] Receipt confirmation works without revealing vote content.

### Administration and Audit

- [ ] Administrator login, OTP, logout and refresh work.
- [ ] Role-based permissions are enforced.
- [ ] Election and candidate management work.
- [ ] Voter management, CSV import and eligibility work.
- [ ] QR generation and download work.
- [ ] Audit events and audit summary work.
- [ ] Turnout API is correct.
- [ ] Full audit-chain verification passes on a clean dataset.

### Verification and Results

- [ ] Election verification checks counts and integrity.
- [ ] Tally decrypts ballots only after closure.
- [ ] Recount matches the primary tally.
- [ ] Finalization is blocked when verification fails.
- [ ] Result publication is permission-controlled.

### Testing and Handover

- [ ] Automated tests pass, including concurrent double-submit tests.
- [ ] Postman evidence is saved.
- [ ] Performance measurements are recorded honestly.
- [ ] OWASP ZAP Baseline Scan report is saved.
- [ ] Recovery test after server interruption is completed.
- [ ] Swagger request and response documentation is correct.
- [ ] API documentation and error-code details are shared with the frontend team.
- [ ] The complete Person 1 and Person 2 workflow is demonstrated.
- [ ] `.env` and private keys are excluded from Git.
- [ ] `.env.example` contains fake values only.
- [ ] `tokens.txt` and local test artifacts are ignored.
- [ ] Known limitations are included in the project report and viva notes.

## 28. Contributors

| Contributor | Responsibility                                                                                                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Person 1    | Administration, authentication, elections, candidates, voters, eligibility, QR generation, shared audit foundation and API documentation                                       |
| Person 2    | QR validation, voter authorization, ballot management, encryption, anonymous vote storage, duplicate prevention, verification, tally, results and security/performance testing |

**GitHub Repository:**
[https://github.com/SreejoySarkar/FINAL_YEAR_PROJECT.git](https://github.com/SreejoySarkar/FINAL_YEAR_PROJECT.git)

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------