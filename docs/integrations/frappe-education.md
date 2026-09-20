# Frappe Education integration

The platform keeps the university's existing academic system as an optional external source instead of replacing it.

## Why this adapter

Frappe Education is an open-source education management system in the Frappe/ERPNext ecosystem. Its documented modules cover student and teacher management, attendance, admissions, course scheduling and a student portal. The project exposes a REST API for DocTypes and supports token authentication. citeturn287615search0turn361916search0

The adapter in `services/api/app/integrations/frappe_education.py` uses the documented REST contract:

- `/api/method/frappe.auth.get_logged_user` for connectivity checks.
- `/api/resource/Student` for student lookup.
- Frappe token authentication using `token api_key:api_secret`.

The connector is tested with an HTTP mock in CI, so the integration contract is validated without contacting a real university system.

## Production configuration

Set these environment variables on a university deployment:

```text
FRAPPE_EDUCATION_BASE_URL=https://university.example.edu
FRAPPE_EDUCATION_API_KEY=...
FRAPPE_EDUCATION_API_SECRET=...
FRAPPE_EDUCATION_STUDENT_NUMBER_FIELD=student_number
```

Real university credentials must be stored in the deployment secret manager, never in Git.

## Licensing boundary

Do not copy Frappe Education source code into this repository as a bundled dependency. Keep the integration at the HTTP boundary and verify the applicable Frappe/ERPNext licenses and commercial terms with counsel before a production commercial deployment.
