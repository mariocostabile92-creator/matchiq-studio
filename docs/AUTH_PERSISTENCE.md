# MatchIQ Studio Auth Persistence

MatchIQ Studio V5.7 supports production-grade auth persistence.

## Local development

When `DATABASE_URL` is not set, users and sessions are stored in:

`storage/auth/matchiq_auth.sqlite3`

## Railway production

For definitive persistence across deploys, restarts and devices:

1. Add a Railway PostgreSQL database to the project.
2. Make sure the web service receives `DATABASE_URL`.
3. Deploy this version.
4. Check `/api/auth/health`.

Expected production response:

```json
{
  "success": true,
  "database": "postgres",
  "persistent": true
}
```

If the response says `sqlite`, the app is still using local storage and Railway can lose users after redeploys.

## Current behavior

- login/register create a 180-day session;
- users are stored in PostgreSQL when `DATABASE_URL` exists;
- local SQLite remains available for development;
- old JSON users/sessions are migrated automatically into the active database on boot.
