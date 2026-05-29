---
name: write-docs
description: Write project documentation and publish to Google Drive as Google Docs (or to docs/ as markdown). Use for runbooks, architecture docs, onboarding guides, or feature documentation.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# /write-docs

> **Local setup:** the Google Drive MCP isn't configured here — default to `--output=markdown` writing into `docs/`. The `--output=drive` path requires the Drive MCP.

You produce well-structured, accurate documentation grounded in the actual codebase. No inventions. No vague promises. Every claim backed by code.

## Invocation

```
/write-docs runbook for payment-svc
/write-docs architecture for the scorecard subsystem
/write-docs onboarding guide for new backend engineers
/write-docs feature doc for F-12 scorecard versioning  --output=drive
/write-docs feature doc for F-12                        --output=local
```

## Output destinations

- `--output=local` (default) — writes markdown to `docs/<filename>.md` in the repo
- `--output=drive` — uses the Google Drive MCP to create a Google Doc in the team's "ServiceCat / Docs" folder
- `--output=both` — writes locally AND publishes to Drive, with the Drive link added to the markdown header

## Document templates

### Runbook
```markdown
# Runbook: <service-name>

**Owner:** <team>
**On-call:** <slack-channel>
**Last updated:** <date>
**Linked CLAUDE.md services entry:** <link>

## What this service does
<1 paragraph, in user-facing terms>

## Architecture summary
<diagram + 2-3 paragraphs>

## How to run locally
<step-by-step>

## Deploys
<which environments, frequency, procedure>

## Common operations
### Restart
### Rollback
### Scale up/down
### Drain a node

## Common alerts and their fixes
| Alert | Likely cause | Action |
|-------|--------------|--------|

## Dependencies
<services this service depends on, services that depend on this service>

## Recent incidents
<links to retros>

## Contact for escalation
<humans + Slack channel>
```

### Architecture document
```markdown
# Architecture: <subsystem>

## Purpose
## Context
## Design
  ### Components
  ### Data flow
  ### Storage model
## Key decisions and tradeoffs
## Out-of-scope considerations
## Open questions
```

### Feature documentation
```markdown
# Feature: <Feature ID> — <Title>

## What it does (user-facing)
## How to use it
  ### Permissions required
  ### UI walkthrough (with screenshots)
  ### API reference
## How it works (engineering-facing)
## Limitations and known issues
## Related features
```

## Process

1. **Read the relevant code** before writing. `/explore-codebase` if unfamiliar.
2. **Read existing docs** to match tone and avoid duplication.
3. **Draft the document** in markdown.
4. **Verify every technical claim** against the code. If you can't verify it, don't write it.
5. **Add diagrams** as Mermaid blocks where they help.
6. **Submit per the chosen output**:
   - Local: write to `docs/<name>.md`, run `/commit-sc docs(...)`
   - Drive: use the Google Drive MCP to create the Google Doc, set sharing to "ServiceCat team — comment"
7. **Output the link or path** to the user

## Quality bar

- **Concrete over abstract** — "POST /scorecards/{id}/runs returns 202 with run_id" not "the runs API can be triggered"
- **Verifiable** — link to code, not to memory
- **Testable** — anyone reading should be able to perform the actions described
- **Up-to-date date stamp** — always include "Last updated"
- **Owner stamp** — always include who owns this doc

## What you must NOT do

- Write speculative docs ("we might add X feature")
- Document private implementation details that change weekly
- Copy someone's doc and rebrand
- Write architecture docs without reading the actual architecture
- Skip the diagram when one would help understanding
- Publish to Drive without proper sharing settings
