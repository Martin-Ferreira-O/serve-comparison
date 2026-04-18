# serve-comparison

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:create_app --factory --reload
```

## Deploy to Vercel

```bash
vercel          # preview deploy
vercel --prod   # production deploy
```

Before the first real sync, operators must populate `COMPARISON_INVITES_PATH` with a flat `{display_name: claim_code}` mapping. Configure this via an environment variable in the Vercel dashboard pointing to a persistent storage location (e.g. Vercel KV, external DB, or a pre-seeded file).

> **Note**: Vercel uses a serverless (ephemeral) filesystem. The SQLite database and invite file will **not persist between requests** in the default setup. For production use, configure an external database such as [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) or [Neon](https://neon.tech).

Each `claim_code` is tied to one preassigned visible name. The first sync must submit the exact visible name paired with that invite code or the hosted service will reject the claim.

Example invite file:

```json
{
  "Martin A.": "invite-123"
}
```

Operational notes:

- Set `COMPARISON_INVITES_PATH` and `COMPARISON_SQLITE_PATH` in the Vercel project environment variables.
- For persistent data, migrate to an external database before opening the service to users.
- Share each invite code together with its exact assigned visible name so the first local sync can claim the right identity.
