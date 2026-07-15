# ScoutAI

Approved Stage 3 foundation is ready for the standalone repository
[`jonniethorpe45-max/ScoutAI`](https://github.com/jonniethorpe45-max/ScoutAI).

The extractable monorepo contents live in [`scoutai/`](./scoutai/) and must be
published at the **ScoutAI repository root** (`apps/`, `packages/`, `docs/`,
`infrastructure/` — not `ScoutAI/scoutai/...`).

## Blocker (Cursor GitHub App)

This cloud agent’s GitHub App installation currently includes only
`Thorpe-Workforce`. Push to ScoutAI returns:

`Permission to jonniethorpe45-max/ScoutAI.git denied to cursor[bot]`

### Unblock — then re-run publish

1. Open GitHub → Settings → Applications → **Cursor** → Configure
2. Grant repository access to **`jonniethorpe45-max/ScoutAI`**
3. Tell the agent to retry publishing Stage 3 to ScoutAI `main`

### Manual publish (personal `gh` login)

Download artifacts from the agent run, then:

```bash
bash publish-ScoutAI-Stage3.sh ./ScoutAI-Stage3-foundation.bundle
```

Or from this tree:

```bash
cd scoutai
# with personal credentials that can write to ScoutAI
git init -b main   # only if starting fresh local mirror
# preferred: use the provided git bundle (preserves Stage 3 commit)
```

Do **not** merge this Thorpe Stage 3 branch into Thorpe `main` as a substitute
for publishing ScoutAI.
