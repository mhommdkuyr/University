# Security

## Production requirements

- Keep API keys, JWT secrets, database passwords and OAuth secrets in the deployment secret manager.
- Never commit the GitHub Default secret or print it in CI logs.
- Put the API behind TLS and a trusted reverse proxy.
- Configure university-specific identity providers and never infer enrollment from a public university number alone.
- Enable database row-level security and verify tenant context on every authenticated transaction.
- Rotate developer/API credentials and provide immediate revocation.
- Rate-limit authentication, AI and public search endpoints.
- Keep audit events immutable and minimize stored personal data.
- AI requests must pass authorization and feature-policy checks before reaching a model provider.
