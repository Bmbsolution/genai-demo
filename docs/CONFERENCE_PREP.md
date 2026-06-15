# Conference Prep — Reading Guide

> Preparation reading for **"Orchestrer l'intelligence : vers des systèmes multi-agents autonomes et collaboratifs"** — Montréal · 18 June 2026.
>
> Curated and ordered so you can read **top to bottom**. Everything here is a primary or authoritative source (Anthropic engineering, the people who coined the terms, the dictionary itself) — no second-hand blog summaries. Core reading is **~3–4 hours**; do at least the 🟢 items.

**Legend** — 🟢 must-read (the spine of the talk) · 🟡 deep-dive (depth for Q&A) · 🔵 reference / hands-on (skim or use while rehearsing). Each entry says *why it matters* and *which slides it backs*.

---

## 1 · The two terms the whole talk hangs on  *(read these first)*

These are slides 3–7. Read the **primary sources** so you can quote them exactly and survive a "well actually" from the audience.

- 🟢 **Andrej Karpathy — the original "vibe coding" tweet** (2 Feb 2025)
  <https://x.com/karpathy/status/1886192184808149383>
  *The exact wording: "fully give in to the vibes… forget that the code even exists." This is slide 4. Quote it verbatim. ~2 min.*

- 🟢 **Simon Willison — "Vibe engineering"** (7 Oct 2025)
  <https://simonwillison.net/2025/Oct/7/vibe-engineering/>
  *The other end of the spectrum — speed **plus** discipline (planning, tests, docs, reviews). This is slides 5–6 and the thesis of your "two cultures." Read in full. ~15 min.*

- 🟢 **Collins Dictionary — Word of the Year 2025: "vibe coding"** (announced 6 Nov 2025)
  <https://blog.collinsdictionary.com/language-lovers/collins-word-of-the-year-2025-ai-meets-authenticity-as-society-shifts/>
  *Backs the "word of the year" claim on slide 4. Skim. ~5 min.* (Press version: [CNN](https://www.cnn.com/2025/11/06/tech/vibe-coding-collins-word-year-scli-intl).)

---

## 2 · The core thesis — orchestration beats intelligence  *(the two most important reads)*

These two Anthropic posts ARE your argument (slides 7–13 and 40: "the leap isn't intelligence, it's orchestration"). If you only read two things, read these.

- 🟢 **Anthropic — Building Effective Agents** (Dec 2024)
  <https://www.anthropic.com/engineering/building-effective-agents>
  *Workflows vs. agents, and the five patterns: prompt chaining, routing, parallelization, **orchestrator–worker**, evaluator–optimizer. Your "loop" and "the orchestrator picks who, when" come straight from here. ~25 min.*

- 🟢 **Anthropic — How we built our multi-agent research system** (June 2025)
  <https://www.anthropic.com/engineering/multi-agent-research-system>
  *A real orchestrator–worker system in production (lead agent + subagents in parallel). Source of the "team of specialists" framing (slide 8) and a concrete result you can cite. ~25 min.*

- 🟡 **Anthropic — Effective context engineering for AI agents** (29 Sep 2025)
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
  *Why a single always-on agent degrades — "context fills with noise over time" (slide 10). The intellectual backing for on-demand sessions. ~20 min.*

---

## 3 · The mechanics you demo — skills, subagents, CLAUDE.md  *(read before rehearsing)*

Directly underpins slides 8–12 ("a skill is a contract," "always-on vs on-demand," the session as the unit of work).

- 🟢 **Anthropic — Equipping agents for the real world with Agent Skills**
  <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>
  *The "skill is a contract, not a prompt" idea (slide 9) and progressive disclosure: metadata ~50 tokens, SKILL.md ~500, resources loaded only when needed. This is your "dormant skill costs ~0 tokens" line (slide 10). ~15 min.*

- 🔵 **Agent Skills — official docs** (the SKILL.md format)
  <https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview>
  *Reference for the exact frontmatter on slide 9 (name / description / allowed-tools). ~10 min.*

- 🟡 **Claude Code — Subagents** (on-call specialists)
  <https://code.claude.com/docs/en/sub-agents>
  *Each subagent = its own context window, tools, permissions — your "agents: spun up for a job, dismissed when done" (slide 8). ~10 min.*

- 🟡 **Claude Code — Best practices for agentic coding** (CLAUDE.md, permissions, the loop)
  <https://code.claude.com/docs/en/best-practices>
  *CLAUDE.md as the "employee handbook every worker reads on day one" (slide 8). ~20 min.*

---

## 4 · The overnight-autonomy demo  *(moment 3)*

- 🟡 **Anthropic — Effective harnesses for long-running agents**
  <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
  *How agents run unsupervised for hours without going off the rails — bounded loops, checkpoints, honest stopping. Backs the "8 gaps · 8 hours · no supervision" demo and the "stopping is a feature" point (slides 13, 17–18). ~20 min.*

---

## 5 · The memory & integration layer

- 🔵 **Anthropic — Introducing the Model Context Protocol** (Nov 2024)
  <https://www.anthropic.com/news/model-context-protocol>
  *The "org layer" of memory on slide 16 (MCP servers · Slack · Drive · GitHub). Enough to explain what MCP is if asked. ~10 min.*

---

## 6 · Hands-on — keep open while you rehearse the live demo

- 🔵 **anthropics/skills** — Anthropic's public Skills, real SKILL.md examples to point at
  <https://github.com/anthropics/skills>
- 🔵 **Claude Agent SDK — overview** (if anyone asks "can I build this myself?")
  <https://code.claude.com/docs/en/agent-sdk/overview>
- 🔵 **anthropic-cookbook — agent patterns** (runnable reference implementations)
  <https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents>

---

## 7 · Q&A ammunition — anticipated question → what to (re)read

Your backup slides are 23–26. Skim the matching source so you answer from knowledge, not memory:

| Backup slide | Question | Read |
|---|---|---|
| 23 | *"Will this replace developers?"* | Willison, *Vibe engineering* (§1) — speed + accountability, humans stay the judgment layer |
| 24 | *"What does it actually cost?"* | *Effective context engineering* (§2) — cost-per-task vs. always-on presence |
| 25 | *"Is our code & data safe?"* | *Agent Skills* + *Subagents* (§3) — scoped `allowed-tools`, isolated contexts |
| 26 | *"What about hallucinations?"* | *Building Effective Agents* (§2) — verification gates; *long-running harnesses* (§4) — bounded retries → escalate |

---

## Citations you can say out loud  *(verified — safe to quote)*

| Claim | Fact | Source |
|---|---|---|
| "vibe coding" coined | Andrej Karpathy, **2 Feb 2025** | [tweet](https://x.com/karpathy/status/1886192184808149383) |
| Word of the Year 2025 | Collins Dictionary, **"vibe coding"**, announced **6 Nov 2025** | [Collins](https://blog.collinsdictionary.com/language-lovers/collins-word-of-the-year-2025-ai-meets-authenticity-as-society-shifts/) |
| "vibe engineering" proposed | Simon Willison, **7 Oct 2025** | [post](https://simonwillison.net/2025/Oct/7/vibe-engineering/) |
| GitHub Copilot | technical preview, **June 2021** | widely documented |
| ChatGPT | launched **30 Nov 2022** | widely documented |
| Claude Code | released **Feb 2025** | noted in Willison's *vibe engineering* post |
| Model Context Protocol | open-sourced by Anthropic, **Nov 2024** | [Anthropic](https://www.anthropic.com/news/model-context-protocol) |
| "Building Effective Agents" | Anthropic engineering, **Dec 2024** | [Anthropic](https://www.anthropic.com/engineering/building-effective-agents) |
| Multi-agent > single-agent | Anthropic's **internal** research eval: lead Opus 4 + Sonnet 4 subagents beat single-agent Opus 4 by **90.2%** | [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system) |

> ⚠️ Two honesty notes for the stage: (1) the **90.2%** figure is Anthropic's *own internal* research benchmark — present it as such, not as a universal number. (2) For jobs/market questions, the data shifts fast — say so and point to primary sources rather than quoting employment stats from memory.

---

*Compiled June 2026. Links verified at time of writing; if a `code.claude.com` doc 404s, start from the [Claude Code docs home](https://code.claude.com/docs).*
