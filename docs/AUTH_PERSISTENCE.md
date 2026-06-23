# MatchIQ Studio Auth Persistence

MatchIQ Studio V5.4 stores users and sessions in `storage/auth/matchiq_auth.sqlite3`.

Important for Railway:
- users stay saved while the server keeps the same persistent storage;
- if Railway redeploys on an ephemeral filesystem without a Volume, the auth database can be recreated empty;
- for production, mount a Railway Volume on the project `storage` folder or move auth to a managed database.

Current MVP behavior:
- login/register create a 180-day session;
- if the same user registers again with the same email and correct password, the app logs them in instead of asking them to create another account;
- old JSON users/sessions are migrated automatically into SQLite on boot.
