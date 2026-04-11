# HackFW 2026 Proposal: MontGoWork

## Fort Worth Workforce Navigation Platform
### Open-source barrier intelligence that gets smarter with every person it helps

---

## The Problem

Fort Worth residents facing unemployment don't have a single barrier — they have a web of them. A criminal record blocks the job. No childcare blocks the interview. No transit blocks the commute. Taking the wrong job triggers a benefit cliff that leaves them worse off than before.

Career centers see this every day. Staff spend hours manually cross-referencing benefits thresholds, job listings, transit routes, legal eligibility, and resource availability — for one person. The next person walks in and they start from scratch.

There is no system that connects barrier assessment, job matching, benefits modeling, and resource routing into a single intelligence layer. And there is no system that learns from each person's outcome to improve guidance for the next.

---

## The Solution: MontGoWork

MontGoWork is an open-source workforce navigation platform that conducts barrier assessment, computes job matches weighted by practical factors (not just skills), screens benefits eligibility with cliff detection, routes criminal records through expungement guidance, and exports actionable plans for both residents and career center staff.

**Proven in Montgomery, Alabama.** 1,391 backend tests. 417 frontend tests. Real deployment. Now porting to Fort Worth as the first city in a framework designed for any city to adopt.

---

## N+1: The Core Insight

Every person who completes the system improves it for the next.

| What N Does | What the System Learns | How N+1 Benefits |
|---|---|---|
| Resolves barriers in a specific sequence | Which resolution order actually works | Gets a better-ordered action plan |
| Takes a job and stays (or doesn't) | Which PVS factors predict retention | Gets more accurate job matches |
| Hits a benefit cliff | The actual threshold and impact | Gets warned earlier with real numbers |
| Uses a resource (or flags it useless) | Which resources deliver vs. waste time | Gets higher-quality referrals |
| Completes expungement | Timeline, steps, and success factors | Gets a realistic roadmap, not a guess |

None of this requires PII. Outcomes feed back as aggregate signal — anonymized barrier graph weights, PVS model tuning, resource rankings. The intelligence is collective. The data stays local.

**Across cities:** Montgomery's barrier resolution patterns inform Fort Worth's. Fort Worth's transit-aware matching informs the next deployment. The network effect IS the product.

---

## Fort Worth-Specific Adaptations

### Transit-Aware Job Matching
Trinity Metro publishes GTFS open data. MontGoWork overlays actual commute time on every job match. "$16/hr but 90 minutes by bus" vs "$15/hr and 20 minutes." PVS scores factor commute burden — because a job you can't get to isn't a job.

### Texas Benefits Modeling
Replace Alabama's 7-program screener with Texas HHSC equivalents: SNAP, TANF, Medicaid, CHIP, childcare subsidy, WIC, LIHEAP. Model the actual Texas thresholds. Build the cliff simulator so residents can see what happens to every benefit when they accept a specific wage.

### Benefit Cliff Simulator
Interactive "what-if" slider: drag the hourly wage, watch benefits phase in and out in real time. Show the math. Show the net-income curve. Identify the safe zones. This is the single highest-anxiety decision for people on benefits — taking a job that might leave them worse off. Make it visible.

### Fair-Chance Employer Index
Fort Worth companies that have signed Ban the Box, participate in second-chance hiring programs, or partner with Workforce Solutions Tarrant. Not a job listing — a trust signal. "These employers actively hire people with records." Built from open data and community validation.

### Barrier Sequencing Engine
The barrier graph isn't just for AI chat — it's a planner. "Fix your record first (free, 6 weeks). Then apply for childcare subsidy (unlocked by clean record). Then target these 3 jobs (now accessible with both resolved)." Show the domino chain. Order matters.

### Community Resource Map
Fort Worth open data + 211 Texas: food banks, childcare centers, legal aid, transit stops. Clustered geographically around the resident's ZIP. Visual, not a list. "Here's everything within 2 miles of you."

### Spanish-Language Native
Fort Worth is ~35% Hispanic. Barrier assessment, AI chat, and action plans work in Spanish from day one. Seed data includes Spanish-language resource variants where available.

### Zero-Friction Entry
No account required to run the full assessment. No PII stored until the resident chooses to save or export. Anonymous mode reduces the trust barrier — critical for people with records, undocumented status, or benefit anxiety.

---

## Technical Architecture

### Stack
- **Frontend:** Next.js 15 (App Router), React, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, Python 3.13, SQLAlchemy (async), SQLite
- **AI:** Multi-provider (Claude, OpenAI, Gemini) with auto-fallback
- **RAG:** FAISS vector store + barrier graph traversal
- **Testing:** 1,391 backend + 417 frontend tests

### Open Data Sources (No Proprietary Scrapers)
| Source | Data |
|---|---|
| Texas Workforce Commission API | State job board listings |
| USAJobs API | Federal positions by location |
| Trinity Metro GTFS | Transit routes, stops, schedules |
| Fort Worth Open Data Portal | City datasets, resources |
| 211 Texas / findhelp.org | Community resources by ZIP |
| JSearch API (RapidAPI) | Aggregated job listings |
| BLS / Data.gov | Labor market statistics by MSA |

### City Framework Architecture
```
cities/
  fort-worth.yaml        # ZIP ranges, coordinates, career center info
  montgomery.yaml        # Original deployment config

data/cities/
  fort-worth/            # Seed data: transit, resources, employers
  montgomery/            # Original seed data

modules/
  benefits/
    texas/               # HHSC program rules, thresholds, cliff model
    alabama/             # Original state benefits
  criminal/
    texas/               # Expunction, nondisclosure, eligibility
    alabama/             # Original state rules
  jobs/
    adapters/
      twc.py             # Texas Workforce Commission adapter
      usajobs.py         # Federal jobs adapter
      jsearch.py         # JSearch adapter (existing)
```

A single environment variable (`CITY=fort-worth`) selects the active city config. Every city-specific component is pluggable. The core engine — barrier assessment, PVS matching, AI chat, PDF export — is city-agnostic.

### N+1 Feedback Architecture
```
Resident completes flow
  -> Anonymized outcome logged (barrier sequence, job match result, resource usage)
  -> Barrier graph weights updated (which sequences resolve fastest)
  -> PVS model coefficients tuned (which factors predict retention)
  -> Resource rankings adjusted (usage + satisfaction signal)
  -> Next resident gets improved recommendations
```

No PII in the feedback loop. Aggregate signal only. Each city deployment contributes to a shared intelligence layer via federated weight sync (optional — cities can run fully isolated).

---

## Sprint Plan (4 Weeks)

### Week 1: Framework Extraction
- Abstract city config from Montgomery hardcoding
- Create `cities/` config schema and `data/cities/` directory structure
- Replace Bright Data integration with open data adapter pattern
- Implement TWC and USAJobs job adapters
- Set up Fort Worth repo (public, MIT license)

### Week 2: Fort Worth Data + Texas Rules
- Build Texas benefits screener (HHSC programs, thresholds)
- Implement Texas expunction/nondisclosure rules
- Ingest Trinity Metro GTFS data
- Compile Fort Worth seed data (career centers, childcare, legal aid, employers)
- Build fair-chance employer index from open sources

### Week 3: New Features
- Benefit cliff simulator (interactive wage slider)
- Transit-aware PVS scoring (GTFS commute overlay)
- Barrier sequencing engine (domino chain planner)
- Living action plan (shareable link, progress tracking)
- Community resource map (geographic clustering)
- Spanish-language support

### Week 4: Polish + Submission
- Anonymous/no-account flow
- Demo video production
- README with setup, usage, deployment specs
- Devpost submission
- Flagship event prep (May 2)

---

## Team

Developed with bpsai-pair (AI-augmented pair programming framework). Driver/Navigator/Reviewer workflow with TDD enforcement, budget tracking, and sprint automation.

---

## Why This Wins

1. **Proven, not theoretical.** Montgomery deployment exists. Tests pass. Real barrier assessment logic. Real benefits screening. This isn't a hackathon prototype — it's a production system being ported.

2. **Open source + open data.** No vendor lock-in. No proprietary scrapers. Any city can fork and deploy. The framework is the product.

3. **N+1 intelligence.** Every resident makes the system smarter for the next one. Across cities, the network effect compounds. This is infrastructure, not an app.

4. **Fort Worth-specific, not generic.** Transit-aware matching via Trinity Metro. Texas HHSC benefits modeling. Fair-chance employer index. Spanish-language native. Built for this city, portable to any city.

5. **Solves a real problem.** Workforce navigation is broken because barriers are interconnected but systems aren't. MontGoWork connects the graph and sequences the path. Career center staff get a tool. Residents get a plan.

---

## Links

- **HackFW 2026:** https://fwtx.devpost.com/
- **Bounties:** https://dao.fwtx.city/bounties
- **Repository:** (to be published)
- **Montgomery Deployment:** (reference available)

---

*MontGoWork: Barrier intelligence that compounds.*
