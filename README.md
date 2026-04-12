# serve-comparison

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:create_app --factory --reload
```

## Deploy to Fly

```bash
fly launch --no-deploy
fly volumes create comparison_data --size 1
fly deploy
```

Before the first real sync, operators must create and populate `COMPARISON_INVITES_PATH` on the mounted volume. By default the app expects `data/comparison_claim_invites.json`, so the deployed service needs that file to exist as a flat `{display_name: claim_code}` mapping before anyone can claim a participant.

Each `claim_code` is tied to one preassigned visible name. The first sync must submit the exact visible name paired with that invite code or the hosted service will reject the claim.

Example invite file:

```json
{
  "Martin A.": "invite-123"
}
```

Operational notes:

- Create `COMPARISON_INVITES_PATH` before opening the service to users.
- Keep the file on persistent storage together with the SQLite database.
- Share each invite code together with its exact assigned visible name so the first local sync can claim the right identity.
