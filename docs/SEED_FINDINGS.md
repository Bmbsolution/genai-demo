# ServiceCat — Seed Findings for Moment 3 (Autonomy Demo)

> The 8 findings used in the autonomy demo (Moment 3 of the conference talk). 7 succeed → 7 PRs. 1 escalates → `needs-human` after 3 attempts. The escalation is intentional — it proves the system knows its limits.

## How to use this file

These findings should be inserted into the database before the demo:

1. Spin up a small fleet of 8 fake "registered services" — actual GitHub repos you control (could be forks of public repos, or deliberately rough demo repos you create). For privacy, avoid using real production services.
2. Run `INSERT INTO findings (...) VALUES (...)` for each finding below — or use a seed script.
3. Pre-record the autonomy run (`/work-findings --max=8`) the night before the talk for the live timelapse.
4. Have the actual GitHub PRs visible (open in tabs) for verification during the talk.

For the live demo magic moment (separate from this), audit a real public repo and trigger `/work-findings` on one specific finding — that PR is opened live in front of the audience.

---

## Demo fleet of services

| Service | Tier | Owner team | Repo URL pattern |
|---------|------|-----------|------------------|
| `payment-svc` | 1 | payments-team | `<your-demo-org>/demo-payment-svc` |
| `notif-svc` | 2 | platform-team | `<your-demo-org>/demo-notif-svc` |
| `gateway` | 1 | platform-team | `<your-demo-org>/demo-gateway` |
| `analytics` | 2 | data-team | `<your-demo-org>/demo-analytics` |
| `legacy-billing` | 2 | billing-team | `<your-demo-org>/demo-legacy-billing` |
| `auth-svc` | 1 | identity-team | `<your-demo-org>/demo-auth-svc` |
| `worker-pool` | 2 | platform-team | `<your-demo-org>/demo-worker-pool` |
| `core-platform` | 1 | platform-team | `<your-demo-org>/demo-core-platform` |

---

## SC-F-1042 — `payment-svc` missing README

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1042
service: payment-svc
scorecard: documentation
criterion_id: doc.readme_present
severity: HIGH
auto_fixable: true
evidence: |
  Repo root has no README.md, README.rst, or README.adoc.
  Last 30 days of commits: 18 — service is active.
remediation: |
  Generate a README.md with the standard sections:
  - What this service does (read package.json description and main module docstrings)
  - Local development setup (read package.json scripts, Makefile, docker-compose.yml)
  - API surface (extract from FastAPI/Express routes if present)
  - Owner team and Slack channel
owner_team: payments-team
expected_outcome: |
  /work-findings inspects the repo, generates a README.md following the
  remediation, opens PR with title "fix(servicecat): add README.md".
  Local tests pass (no tests are affected by docs).
  PR successfully opened, awaiting human review.
```

---

## SC-F-1051 — `notif-svc` missing OpenAPI spec

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1051
service: notif-svc
scorecard: documentation
criterion_id: doc.openapi_spec
severity: HIGH
auto_fixable: true
evidence: |
  No openapi.yaml, openapi.json, or swagger.yaml in repo.
  FastAPI app does not expose /openapi.json (verified by grep for FastAPI()).
  This is an Express service — must be hand-authored or generated from JSDoc.
remediation: |
  This is an Express service. Generate openapi.yaml using swagger-jsdoc by:
  1. Add swagger-jsdoc and swagger-ui-express to dependencies
  2. Annotate routes in src/routes/*.js with JSDoc @swagger blocks
  3. Add a setup function in src/openapi.js that scans routes
  4. Mount /api-docs at startup
  5. Generate openapi.yaml and commit alongside
owner_team: platform-team
expected_outcome: |
  /work-findings adds the dependencies, annotates routes, generates the spec,
  opens PR. Tests pass (route changes are additive).
```

---

## SC-F-1063 — `gateway` missing security headers in nginx

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1063
service: gateway
scorecard: security
criterion_id: sec.security_headers
severity: HIGH
auto_fixable: true
evidence: |
  nginx/default.conf serves on port 443 but lacks:
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: strict-origin-when-cross-origin
  - Content-Security-Policy: <project default>
  - Strict-Transport-Security: max-age=31536000; includeSubDomains
remediation: |
  Add the standard security headers block. The project has a template at
  templates/nginx-secure-headers.conf that can be included via:
    include /etc/nginx/conf.d/secure-headers.conf;
  CSP value should be the project default policy (deny-by-default + allow-list
  for known assets origins).
owner_team: platform-team
expected_outcome: |
  /work-findings copies the standard headers block into nginx/default.conf,
  validates with `nginx -t`, opens PR.
  Note: the agent should NOT change CSP defaults without team review — the
  project default is conservative and that's intentional.
```

---

## SC-F-1077 — `analytics` CI runs no tests on Python 3.12

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1077
service: analytics
scorecard: reliability
criterion_id: rel.ci_python_version
severity: HIGH
auto_fixable: true
evidence: |
  .github/workflows/test.yml runs on python-version: 3.10 only.
  setup.py / pyproject.toml lists "python_requires=>=3.10" — should support 3.12.
  No matrix testing across Python versions.
remediation: |
  Update CI workflow to test against Python 3.10, 3.11, and 3.12 in a matrix.
  Verify all dependencies in pyproject.toml are 3.12-compatible.
  Update python_requires if needed (likely fine as-is).
owner_team: data-team
expected_outcome: |
  /work-findings updates the matrix in test.yml, runs locally to verify all
  tests pass on Python 3.12 (using pyenv if available, else trust the agent's
  reading of dependencies), opens PR.
```

---

## SC-F-1082 — `legacy-billing` no CODEOWNERS file

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1082
service: legacy-billing
scorecard: documentation
criterion_id: doc.codeowners
severity: MEDIUM
auto_fixable: true
evidence: |
  No .github/CODEOWNERS file.
  Service has 3 active contributors in last 90 days, all from billing-team.
  This means PRs auto-route to no one — review responsibility is unclear.
remediation: |
  Create .github/CODEOWNERS with:
    *  @<your-org>/billing-team
  Use the team's GitHub team handle (look up via `gh api orgs/<org>/teams`).
  Verify the team has write access to the repo.
owner_team: billing-team
expected_outcome: |
  /work-findings creates CODEOWNERS with the team handle, opens PR.
  Tests pass (this is a metadata-only change).
```

---

## SC-F-1095 — `auth-svc` runbook outdated (>180 days)

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1095
service: auth-svc
scorecard: documentation
criterion_id: doc.runbook_freshness
severity: MEDIUM
auto_fixable: true
evidence: |
  RUNBOOK.md exists but last commit to it was 2025-09-12 (240 days ago).
  Service has had 47 commits since (excluding doc commits).
  Likely outdated: it still references the old AWS region and an old
  on-call channel name.
remediation: |
  Regenerate the runbook from current code:
  1. Read current architecture (main.py, routes, dependencies)
  2. Read current docker-compose.yml and CI workflow for deploy procedure
  3. Read team config in ServiceCat for current Slack channel
  4. Preserve any "Common alerts" entries — those have institutional knowledge
  5. Update the "Last updated" stamp
remediation_note: |
  The agent must NOT discard the existing alerts table — those entries are
  hand-authored institutional knowledge. Merge, don't replace.
owner_team: identity-team
expected_outcome: |
  /work-findings reads the existing runbook, identifies stale sections,
  regenerates them while preserving the alerts section, opens PR.
```

---

## SC-F-1108 — `worker-pool` missing health check endpoint

**Outcome:** ✅ PR opens, succeeds.

```yaml
finding_id: SC-F-1108
service: worker-pool
scorecard: reliability
criterion_id: rel.healthcheck
severity: HIGH
auto_fixable: true
evidence: |
  k8s deployment lacks readinessProbe and livenessProbe.
  Service code has no /health or /healthz endpoint (grep across src/).
  This means Kubernetes can't detect crashed workers — they accumulate as
  zombie pods.
remediation: |
  1. Add a /healthz endpoint that returns 200 if the worker can connect to
     Redis (the queue backend) and 503 if not.
  2. Add readinessProbe to k8s/deployment.yaml: HTTP GET /healthz, every 10s.
  3. Add livenessProbe: same, but with longer timeout.
owner_team: platform-team
expected_outcome: |
  /work-findings adds the endpoint with a Redis ping, updates k8s manifest,
  adds tests for both healthy and unhealthy states, opens PR.
```

---

## SC-F-1124 — `core-platform` config loader complexity ⚠️ ESCALATES

**Outcome:** ⚠️ Escalates to `needs-human` after 3 attempts.

```yaml
finding_id: SC-F-1124
service: core-platform
scorecard: quality
criterion_id: quality.cyclomatic_complexity
severity: HIGH
auto_fixable: true     # Marked auto-fixable, but in practice it isn't.
evidence: |
  src/config/loader.py has cyclomatic complexity 47 (threshold: 15).
  The function load_config() handles 12 sources (env, yaml, vault, k8s
  ConfigMap, AWS Parameter Store, file, default, override, etc.) with deeply
  nested if/else.
  No single small fix — this needs an architectural decision.
remediation: |
  Refactor into a plugin architecture: BaseConfigSource interface + one class
  per source. Resolution happens via a chain-of-responsibility.
remediation_note: |
  This is not a "small fix" — it's a redesign. The agent will try, fail,
  and escalate. That's the correct behavior.
owner_team: platform-team

expected_outcome:
  attempt_1: |
    Agent reads loader.py. Tries to extract sources into separate functions.
    The functions still depend on shared state in subtle ways — tests fail.
    Reverts.
  attempt_2: |
    Agent tries a thinner refactor: just extract two of the simpler sources
    (env and file) into helpers. Tests pass for those, but other sources
    still violate the threshold.
    Function complexity is still 39 — above threshold. Doesn't resolve the
    finding.
  attempt_3: |
    Agent attempts the full plugin architecture. Multiple test failures from
    initialization order changes. Reverts.
  resolution: |
    After 3 attempts, /work-findings marks the finding "needs-human".
    Comments on finding with:
      "Attempted 3 refactors (extract-helpers, partial-extraction, plugin-architecture).
       All produced regressions or failed to fully resolve.
       This needs an architectural decision: which sources are first-class plugins,
       and how to handle initialization order. Recommend: tech lead pairs with
       agent on a planning session, or breaks this into smaller staged refactors
       under a parent issue."
    Sends Slack to platform-team channel.
    Adds 'needs-human' label to the linked GitHub issue.
    Moves to next finding (none — queue is empty after this).
```

### Why this escalation is the most important moment of the demo

Every other finding shows the system getting things done. This one shows the system **knowing what it can't do** and **asking honestly** rather than guessing. That's the difference between a tool that works on the demo and a tool you can deploy.

When you walk through the timelapse: spend 30 seconds on each successful finding, then **slow down for SC-F-1124**. Show the comment trail. Show the escalation Slack message. Make the point:

> "Anyone can build an agent that succeeds when the path is clear. The interesting engineering is the agent that knows when to stop. ServiceCat's `/work-findings` agent is allowed three attempts. After that, it tells you what it tried and what it learned, and gets out of your way. This is what makes it deployable."

---

## Pre-demo checklist

Before the talk:

- [ ] All 8 demo repos exist on GitHub and are accessible
- [ ] All 8 findings inserted in the demo workspace database
- [ ] `/work-findings --max=8` runs to completion in <8 hours of wall time (use sleep mocks if needed)
- [ ] All 7 successful PRs are real and visible on GitHub
- [ ] The escalation Slack message is in a real Slack workspace you can show
- [ ] Backup video recorded in case live network fails

---

## After the demo

These findings can be reset for the next time. The reset script:

```sql
UPDATE findings
SET status = 'open', pr_url = NULL, attempts = 0
WHERE finding_id IN (
  'SC-F-1042', 'SC-F-1051', 'SC-F-1063', 'SC-F-1077',
  'SC-F-1082', 'SC-F-1095', 'SC-F-1108', 'SC-F-1124'
);

DELETE FROM audit_logs
WHERE resource_id IN (
  'SC-F-1042', 'SC-F-1051', 'SC-F-1063', 'SC-F-1077',
  'SC-F-1082', 'SC-F-1095', 'SC-F-1108', 'SC-F-1124'
);
```

And on GitHub:
```bash
# Close the demo PRs without merging
for pr in 87 88 89 90 91 92 93; do
  gh pr close $pr --comment "Demo PR — closing for next run"
done
```
