# GoWork Press Kit (HackFW 2026)

---

## One-Liner

Workforce navigator that hands you a same-day case file -- not a 12-week plan.

---

## What It Is

GoWork is a full-stack workforce navigation platform built for Fort Worth, Texas (HackFW 2026 submission). People facing employment barriers don't just need a job listing. They need someone to do the math. What happens to your SNAP if you take a $15/hr job. Whether Trinity Metro Bus 4 actually gets you there by 7am. Which employers run background checks and which ones don't.

Career center staff do this work manually, every day, for every person who walks in. GoWork does it the same day.

A resident completes a guided assessment covering seven barrier types (credit, transportation, childcare, housing, health, training, criminal record). The system generates a personalized case file. Jobs ranked by a Practical Value Score. Benefits eligibility with cliff detection across Texas programs. Criminal record routing with Article 55 expunction + Chapter 411 nondisclosure guidance. AI-powered barrier intelligence chat. And a printable Career Center Ready Package the resident hands to a case worker -- the same day.

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
| Texas benefits programs screened | SNAP, Medicaid, CHIP, TANF, Texas Workforce, child care subsidy |
| LLM providers | 3 (Claude, OpenAI, Gemini) with auto-fallback |
| Job sources | Texas Workforce Commission, USAJobs |
| Fort Worth poverty rate (76104, 76119) | 23%+ |
| Labor participation rate (target ZIPs) | <60% |

---

## What It Actually Does

**Barrier Assessment Wizard.** 7-step guided assessment. ZIP validation, resume upload, barrier selection, benefits data, schedule constraints, industry preferences, review and submit. Each barrier type maps to specific resources, job filters, and action items.

**Practical Value Score.** Jobs ranked by what actually matters. Net income after benefits impact (35%), proximity and transit access (25%), schedule fit (20%), barrier compatibility (20%). Not "here are jobs in your area." Here are jobs you can get to, keep, and live on.

**Benefits Cliff Detection.** Calculates net income at each wage step. Shows exactly where a raise triggers a benefits drop that leaves you worse off. Residents see the math before they accept an offer.

**Criminal Record Routing.** Employer background check policy matching. Fair-chance employer filtering. Expunction (Texas Article 55) + nondisclosure (Texas Government Code Chapter 411) eligibility screening. Doesn't just say "you have a record." Shows which doors are actually open.

**AI Barrier Intelligence Chat.** Multi-provider LLM with RAG-powered context from Fort Worth resource data. FAISS vector store plus barrier graph traversal. Topic guardrails keep conversations on track. Streaming responses.

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

GoWork was built using PairCoder's enforcement workflow. The test suite isn't afterthought coverage. Every feature started as a failing test. The barrier graph, PVS scoring, benefits cliff calculations, and expunction/nondisclosure routing all have deterministic test coverage because the enforcement layer required it before any code shipped.

---

## The Problem

Career centers see the same pattern every day. Someone walks in needing a job, but it's never just about the job. No car means no commute. No childcare means no interview. A criminal record means half the listings don't apply. Taking the wrong job triggers a benefits cliff that leaves them poorer than they were.

Staff spend hours cross-referencing benefits thresholds, job listings, transit routes, legal eligibility, and local resources. For one person. Then the next person walks in and they start over.

GoWork replaces that manual process with structured assessment and intelligent matching. The resident gets a same-day case file. The staff get a briefing. The career center gets throughput.

---

## Screenshots

1. **The Wall (Ch1)** (press-01-landing.png)
   "What's standing between you and a job?" The cinematic hero question over a Mapbox-rendered Fort Worth.

2. **Assessment Wizard, Step 1** (press-02-basic-info.png)
   ZIP code validation, employment status, vehicle access. 7-step stepper.

3. **Barrier Selection** (press-step3-whatsinyourway.png)
   "What's in your way?" Seven barrier cards with icons. Credit, Transportation, Childcare, Housing, Health, Training, Criminal Record.

4. **The Wall (Any City)** (07-landing-full.png)
   Texas-region overview. Fort Worth lit, five Texas cities (Dallas, Houston, Austin, San Antonio, Waco) on deck.

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
