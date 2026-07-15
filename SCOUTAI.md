# ScoutAI

This repository currently hosts a **standalone ScoutAI scaffold** at [`scoutai/`](./scoutai/).

Cursor cloud agents in this environment cannot create new GitHub repositories
(the install token lacks `POST /user/repos`). To publish ScoutAI as its own repo:

```bash
cd scoutai
bash scripts/create-github-repo.sh
```

That creates `https://github.com/jonniethorpe45-max/ScoutAI` and pushes a clean `main` history.
