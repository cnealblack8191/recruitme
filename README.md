# RecruitMe

ECI's recruiting research application: profile-driven candidate discovery, evidence-based qualification, recruiter review, and bounded AWS worker execution.

## Start here

- [Product and engineering brief for Claude](RecruitMe-Claude-Review-Brief.md)
- [Integration report and known release blockers](RECRUITME-INTEGRATION-REPORT.md)
- [Central staff application](central/README.md)
- [Python worker](recruitme-upgrade/README.md)
- [Qualification policy](recruitme-upgrade/QUALIFICATION.md)

This repository is a clean source snapshot published September 16, 2026 from the Candidate Portal integration workspace (base commit `52b995e`), including subsequent local provider changes and the Central application. It does not include the original repository's Git history, production credentials, candidate databases, search output, dependency folders, or generated builds. Historical documents describe different stages; the review brief reconciles major differences.

## Layout

| Directory | Purpose |
| --- | --- |
| `client/` | React Candidate Portal and RecruitMe screens |
| `server/`, `shared/` | Express/tRPC services, validation, shared contracts |
| `central/` | Separate staff frontend/server and password authentication |
| `recruitme-upgrade/recruitme/` | Python search worker, adapters, budgets, evidence, qualification |
| `recruitme-upgrade/tests/` | Worker regression tests |
| `drizzle/` | Candidate Portal database schema and migrations |

## Development

Use a modern Node.js runtime, the pnpm version pinned in `package.json`, and Python 3. Linux is required for worker locking, signal, and systemd-specific validation. Install JavaScript dependencies from the committed lockfile:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

The existing `dev` and `start` scripts use POSIX environment assignment; on Windows use WSL or set `NODE_ENV` in PowerShell before invoking the underlying `tsx`/Node command.

This is not a zero-configuration hosted app. The original portal expects a configured MySQL database, authentication services, and environment variables read in `server/_core/env.ts`. Central uses its own password flow or the existing loopback staff identity service; see `central/README.md`. Provider credentials, AWS access, state directories, worker configuration, and bridge commands must be provisioned separately. Keep the bridge disabled during initial local review. Do not replay historical remote scripts as a deployment procedure.

Build and check the web application:

```sh
pnpm build
pnpm check
pnpm test
pnpm test:frontend
```

Build Central separately:

```sh
pnpm exec vite build --config central/vite.config.ts
pnpm exec esbuild central/server.ts --bundle --platform=node --format=esm --packages=external --outfile=central-dist/server.mjs
```

Run worker tests from `recruitme-upgrade/`:

```sh
python -B -m unittest discover -s tests -v
```

## Current validation status

The September 13 integration report records successful worker tests, RecruitMe-specific backend/frontend tests, and production builds, but also database-dependent backend failures, 12 shared UI type errors, and unverified deployed controls. Those results predate subsequent provider changes. This publication is a source handoff, not a new release certification or deployment. See the integration report for exact counts and remaining issues.

## Data and operational boundaries

Search records are not verified candidates. Human review is required for verified evidence and qualification. Provider usage is subject to explicit run/session budgets, pricing validity, and request limits. No provider is configured merely by cloning this repository. Do not commit credentials, session files, private candidate data, or worker ledgers.
