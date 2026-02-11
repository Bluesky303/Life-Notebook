# Git Branch Workflow

This repository follows `main -> dev -> feature/*`.

## Branch Roles
- `main`: production/stable code only.
- `dev`: integration branch for reviewed feature work.
- `feature/<name>`: isolated development branch for one feature/fix.

## Required Flow
1. Create feature branch from `dev`.
2. Develop and commit on `feature/<name>`.
3. Push feature branch and open PR to `dev`.
4. After review and merge into `dev`, run integration testing on `dev`.
5. When ready for release, open PR from `dev` to `main`.

## Issue-Driven Workflow
1. Create (or select) a GitHub Issue for the task.
2. Apply labels (at minimum one `priority:*` label and one type label such as `feat`/`bug`).
3. Create branch from `dev` using issue ID:
   - `feature/<issue-id>-<short-name>`
4. Implement changes in that feature branch only.
5. Open PR from feature branch to `dev` and link the issue (`Closes #<id>` in PR body).
6. Wait for maintainer review and merge approval.
7. Promote `dev -> main` only after validation/testing.

## Command Examples
```bash
# update local branches
git checkout dev
git pull origin dev

# create feature branch
git checkout -b feature/knowledge-markdown-preview

# after development
git add .
git commit -m "feat: improve markdown preview for knowledge pages"
git push -u origin feature/knowledge-markdown-preview
```

## Pull Request Rules
- Feature PR target branch must be `dev`.
- Do not push unfinished feature work directly to `dev` or `main`.
- `main` only accepts tested changes from `dev`.
- Every feature/fix should map to a GitHub Issue.
- PR description should include: scope, risk, test result, and linked issue.

## Codex Execution Policy
- Codex should work by: create/update issue -> create `feature/*` branch -> implement -> push -> open PR to `dev`.
- Codex does not merge PRs to `dev` or `main` without maintainer approval.
- Maintainer reviews PR first; merge is manual after approval.

## Docs-Only Exception Flow
Use this flow only for documentation-only changes (no runtime code changes):
1. Create a docs issue and label with `docs` (+ optional priority label).
2. Branch from `dev` using issue id:
   - `feature/<issue-id>-docs-<short-name>`
3. Open PR to `dev` and link the issue (`Closes #<id>`).
4. If maintainer explicitly allows self-merge for this docs task:
   - merge the PR to `dev` by yourself,
   - delete remote feature branch,
   - delete local feature branch,
   - confirm issue is closed.
5. Return to `dev` and sync:
   - `git checkout dev && git pull origin dev`

Docs-only exception must not be used for frontend/backend/runtime behavior changes.

## CI/CD (Planned)
- Add CI on PR to `dev`: lint + tests + build.
- Add release workflow on merge `dev -> main`.
