Secure E-Voting System – API Documentation

Base URL: http://127.0.0.1:8000/api/


1. ADMIN AUTHENTICATION

| HTTP Method | Endpoint             | Purpose                  |
|-------------|----------------------|--------------------------|
| POST        | /admin/login         | Admin login              |
| POST        | /admin/verify-otp    | Verify OTP               |
| POST        | /admin/logout        | Admin logout             |
| POST        | /admin/token/refresh | Refresh access token     |


2. ELECTIONS AND CANDIDATES

| HTTP Method | Endpoint                       | Purpose                  |
|-------------|--------------------------------|--------------------------|
| GET         | /elections/                    | View all elections       |
| POST        | /elections/                    | Create an election       |
| GET         | /elections/{id}/               | View election details    |
| PUT/PATCH   | /elections/{id}/               | Update an election       |
| DELETE      | /elections/{id}/               | Delete an election       |
| POST        | /elections/{id}/publish/       | Publish an election      |
| POST        | /elections/{id}/close/         | Close an election        |
| GET         | /candidates/                   | View candidates          |
| POST        | /candidates/                   | Add a candidate          |
| GET         | /elections/{id}/candidates     | View election candidates |


3. VOTERS AND ELIGIBILITY

| HTTP Method | Endpoint                              | Purpose                    |
|-------------|---------------------------------------|----------------------------|
| GET         | /voters/                              | View all voters            |
| POST        | /voters/                              | Add a voter                |
| POST        | /voters/import                        | Import voters              |
| GET         | /elections/{id}/eligible-voters       | View eligible voters       |
| POST        | /elections/{id}/eligible-voters       | Add eligible voters        |
| GET         | /elections/{id}/eligibility/check     | Check voter eligibility    |


4. QR TOKEN MANAGEMENT

| HTTP Method | Endpoint                                      | Purpose                  |
|-------------|-----------------------------------------------|--------------------------|
| POST        | /elections/{id}/generate-qr                   | Generate QR tokens       |
| GET         | /elections/{id}/voters/{voter_id}/qr          | Download voter QR code   |


5. AUDIT LOGS

| HTTP Method | Endpoint          | Purpose                     |
|-------------|-------------------|-----------------------------|
| GET         | /audit-logs       | View audit logs             |
| GET         | /audit-logs/verify| Verify audit log integrity  |


6. API DOCUMENTATION

| HTTP Method | Endpoint | Purpose                   |
|-------------|----------|---------------------------|
| GET         | /schema/ | View API schema           |
| GET         | /docs/   | Open Swagger documentation|


7. AUTHENTICATION

| Item              | Details                                 |
|-------------------|-----------------------------------------|
| Authentication    | JWT access token                        |
| Header            | Authorization: Bearer YOUR_ACCESS_TOKEN |
| OTP Verification  | Required during admin login             |


8. IMPORTANT NOTES

- Admin login requires OTP verification.
- API permissions depend on the admin role.
- Election management is restricted to authorized admins.
- QR tokens are election-specific.
- Never share passwords, OTPs, JWT tokens or secret keys publicly.