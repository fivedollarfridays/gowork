# MontGoWork Press Kit

---

## One-Liner

Open-source workforce navigator that turns a 2-hour career center intake into a 10-minute personalized plan.

---

## What It Is

MontGoWork is a full-stack workforce navigation platform built for Montgomery, Alabama. People facing employment barriers don't just need a job listing. They need someone to do the math. What happens to your SNAP if you take a $15/hr job. Whether the bus actually gets you there by 7am. Which employers run background checks and which ones don't.

Career center staff do this work manually, every day, for every person who walks in. MontGoWork does it in minutes.

A resident completes a guided assessment covering seven barrier types (credit, transportation, childcare, housing, health, training, criminal record). The system generates a personalized re-entry plan. Jobs ranked by a Practical Value Score. Benefits eligibility across 7 Alabama programs with cliff detection. Criminal record routing with expungement guidance. AI-powered barrier intelligence chat. And a printable Career Center Ready Package they take to the career center on Monday morning.

---

## Accolade

**2nd Place, Worldwide Vibes Hackathon**

---

## Source

GitHub: https://github.com/fivedollarfridays/montgowork

---

## Numbers

| | |
|---|---|
| Barrier types assessed | 7 |
| Alabama benefits programs screened | 7 (SNAP, TANF, Medicaid, ALL Kids, Childcare Subsidy, Section 8, LIHEAP) |
| Backend tests | 1,391 |
| Frontend tests | 417 |
| Total tests | 1,808 |
| LLM providers | 3 (Claude, OpenAI, Gemini) with auto-fallback |
| Job sources | 3 (BrightData, JSearch, Honest Jobs) |
| Montgomery poverty rate | 20.9% |
| Labor participation rate | 57.5% |
| Residents in service area | 36,000+ |

---

## What It Actually Does

**Barrier Assessment Wizard.** 7-step guided assessment. ZIP validation, resume upload, barrier selection, benefits data, schedule constraints, industry preferences, review and submit. Each barrier type maps to specific resources, job filters, and action items.

**Practical Value Score.** Jobs ranked by what actually matters. Net income after benefits impact (35%), proximity and transit access (25%), schedule fit (20%), barrier compatibility (20%). Not "here are jobs in your area." Here are jobs you can get to, keep, and live on.

**Benefits Cliff Detection.** Calculates net income at each wage step. Shows exactly where a raise triggers a benefits drop that leaves you worse off. Residents see the math before they accept an offer.

**Criminal Record Routing.** Employer background check policy matching. Fair-chance employer filtering. Expungement eligibility screening under Alabama Act 2021-507. Doesn't just say "you have a record." Shows which doors are actually open.

**AI Barrier Intelligence Chat.** Multi-provider LLM with RAG-powered context from Montgomery resource data. FAISS vector store plus barrier graph traversal. Topic guardrails keep conversations on track. Streaming responses.

**Career Center Ready Package.** Two-part printable PDF. Part one is the staff summary: barriers, WIOA eligibility, recommended next steps. Part two is the resident action plan: document checklist, what to say, what to expect. A resident walks into the career center with everything staff need to help them right away.

**WIOA Eligibility Screening.** Automated screening for Adult Program, Supportive Services, Individual Training Accounts, and Dislocated Worker programs.

---

## Stack

| Layer | What |
|-------|------|
| Frontend | Next.js 15 (App Router), React, Tailwind, shadcn/ui |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), SQLite |
| AI | Claude, OpenAI, Gemini (multi-provider, auto-fallback) |
| RAG | FAISS vector store + barrier graph (DAG) traversal |
| Jobs | BrightData Datasets API, JSearch, Honest Jobs |
| PDF | html2pdf.js + qrcode.react |
| Tests | pytest (1,391) + Vitest (417) |

---

## Built With PairCoder

MontGoWork was built using PairCoder's enforcement workflow. The 1,808-test suite isn't afterthought coverage. Every feature started as a failing test. The barrier graph, PVS scoring, benefits cliff calculations, and expungement routing all have deterministic test coverage because the enforcement layer required it before any code shipped.

---

## The Problem

Career centers see the same pattern every day. Someone walks in needing a job, but it's never just about the job. No car means no commute. No childcare means no interview. A criminal record means half the listings don't apply. Taking the wrong job triggers a benefits cliff that leaves them poorer than they were.

Staff spend hours cross-referencing benefits thresholds, job listings, transit routes, legal eligibility, and local resources. For one person. Then the next person walks in and they start over.

MontGoWork replaces that manual process with structured assessment and intelligent matching. The resident gets a plan. The staff get a briefing. The career center gets throughput.

---

## Screenshots

1. **Landing Page** (press-01-landing.png)
   "What's standing between you and a job?" Hero with How It Works flow and Montgomery workforce statistics.

2. **Assessment Wizard, Step 1** (press-02-basic-info.png)
   ZIP code validation, employment status, vehicle access. 7-step stepper.

3. **Barrier Selection** (press-step3-whatsinyourway.png)
   "What's in your way?" Seven barrier cards with icons. Credit, Transportation, Childcare, Housing, Health, Training, Criminal Record.

4. **Full Landing** (07-landing-full.png)
   Complete view with hero, How It Works, and Montgomery by the Numbers stats.

---

## Quote

"Hackathon project turned enforcement-driven civic tech." — Kevin Masterson

---

## Team

- **Kevin Masterson** Creator, lead developer
- **Shawn Sanchez** Co-developer, current project lead

---

## Contact

- **Reddit:** u/macaulay_codin
- **X:** @paircoder
- **GitHub:** https://github.com/fivedollarfridays
- **Subreddit:** r/PairCoder

---

## License

MIT

---

*Last updated: 2026-04-12*
