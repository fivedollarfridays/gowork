# GoWork Demo Script (HackFW 2026)

> 3-minute live demo + 2-minute Q&A. Single persona for the hackathon submission: **Carlos (Fort Worth)**. The legacy Montgomery, AL persona (Maria) is available for non-HackFW demos but is NOT part of the HackFW 2026 narrative.

---

## Pre-Demo Checklist

- [ ] Backend running: `cd backend && CITY=fort-worth uvicorn app.main:app --reload` (port 8000)
- [ ] Frontend running: `cd frontend && npm run dev` (port 3000)
- [ ] `ANTHROPIC_API_KEY` set in `backend/.env` (for AI narrative)
- [ ] Database auto-seeds on first startup (resources, transit routes -- no manual step needed)
- [ ] Browser at `http://localhost:3000`, zoomed to 125% for visibility
- [ ] Screen sharing active, dark/light mode matches projector

---

## Primary Persona: Carlos (Fort Worth / HackFW 2026)

| Field | Value |
|-------|-------|
| Name | Carlos |
| Age | 29 |
| Location | Fort Worth, TX (ZIP 76119) |
| Situation | Recently released, single father of 1 |
| Vehicle | No |
| Employment | Unemployed |
| Work history | 4 years warehouse and logistics before incarceration |
| Credit score | ~540 (Very Poor) |
| Utilization | 72% |
| Payment history | 68% on-time |
| Account age | 1-3 years |
| Accounts | 3 total, 1 open, 1 in collections |
| Negative items | Late payments, collections |
| Barriers | Credit, Transportation, Childcare, Criminal Record |

---

## Demo Flow (3 minutes)

### 1. Landing Page (0:00 - 0:15)

**URL:** `http://localhost:3000`

**Click:** "Get Your Plan" button (hero section)

**Say:**
> "Meet Carlos. He's 29, lives in Fort Worth, just came home from incarceration. One kid, no car, credit score around 540. He's got real barriers -- but he's ready to work. Let's see what MontGoWork does for him."

**Highlight:** The three-step flow cards (Assess, Match, Plan) and Fort Worth stats (15.3% poverty, 64% labor participation, 950K+ metro population).

---

### 2. Basic Info -- Step 1 (0:15 - 0:30)

**Page:** `/assess` -- Step 1 of wizard

**Actions:**
1. Type `76119` in ZIP Code field
2. Select "Unemployed" from Employment dropdown (already default)
3. Leave "I have a vehicle" unchecked
4. Click "Next"

**Say:**
> "ZIP 76119 -- southeast Fort Worth. Unemployed, no vehicle. That tells us he needs Trinity Metro transit routes and barrier-compatible employers near transit stops."

**Highlight:** ZIP validation (only accepts Fort Worth-area 761xx codes).

---

### 3. Barriers -- Step 2 (0:30 - 0:50)

**Page:** `/assess` -- Step 2 of wizard

**Actions:**
1. Click "Credit / Financial" card
2. Click "Transportation" card
3. Click "Childcare" card
4. Click "Criminal Record" card
5. Click "Next"

**Say:**
> "Four barriers. Credit history, no car, needs childcare, and a criminal record. The severity badge updates live -- four barriers is 'high' severity. The system will prioritize resources for his most critical needs."

**Highlight:** Severity badge changing as barriers are selected. Cards highlight with checkmarks.

---

### 3b. Criminal Record -- Step 2b (conditional)

**Page:** `/assess` -- Criminal record form (only appears because criminal record barrier was selected)

**Actions:**
1. Select "Misdemeanor" from record type
2. Select "Theft" from charge category
3. Enter **3** years since conviction
4. Check "Sentence completed"
5. Click "Next"

**Say:**
> "Because he selected criminal record, he gets an extra step. Misdemeanor theft, 3 years ago, sentence complete. The system checks Texas Government Code Chapter 411 Subchapter E-1 for nondisclosure eligibility -- he may qualify to seal his record. It also checks Article 55 expunction. And it filters employers by their fair-chance hiring policies."

**Highlight:** This step is conditional -- only appears when criminal record barrier is selected.

---

### 4. Credit Check -- Step 3 (0:50 - 1:20)

**Page:** `/assess` -- Step 3 (only appears because credit barrier was selected)

**Actions:**
1. Drag credit score slider to **540** (should show "Very Poor" in red)
2. Drag utilization slider to **72%** (shows red -- above 30% threshold)
3. Drag payment history to **68%**
4. Select "1-3 years" from account age dropdown
5. Enter **3** total accounts, **1** open, **1** in collections
6. Check "Late Payments" and "Collections" under negative items
7. Click "Next"

**Say:**
> "Self-reported credit assessment -- no hard pull, no SSN. Score of 540, high utilization, late payments and collections. The system uses this to separate which employers he can apply to NOW versus which ones unlock after credit repair."

**Highlight:** The color-coded score band (Very Poor = red), utilization turning red above 30%.

---

### 5. Review & Submit -- Step 4 (1:20 - 1:40)

**Page:** `/assess` -- Step 4 of wizard

**Actions:**
1. Type in Work History: `4 years warehouse at Amazon FC (DFW5). Forklift certified. Loading dock experience.`
2. Review the summary card (ZIP, Employment, Barriers, Vehicle, Credit Score)
3. Click "Submit Assessment"

**Say:**
> "He adds his work history -- warehouse logistics and forklift cert. That opens up logistics jobs along the Trinity Metro 6 and 8 routes. The summary shows everything. When he submits, the backend scores his profile, runs matching filters, checks Texas benefits eligibility, and builds a personalized plan -- all in one request."

**Highlight:** The summary card with all data. Loading spinner with "Analyzing your profile..."

---

### 6. Plan View -- Monday Morning (1:40 - 2:10)

**Page:** `/plan?session=<id>` -- auto-redirected after submit

**Say:**
> "Here's the magic. 'What you can do Monday morning.' The AI writes a personalized narrative -- not generic advice, but Fort Worth-specific. It knows about Trinity Metro routes, the Workforce Solutions office on E. Belknap, HHSC for benefits, Legal Aid of NorthWest Texas for record clearing. Every action step has a phone number, address, or link."

**Highlight:**
- AI narrative card with sparkle icon (may show loading spinner briefly)
- "Key Actions" cards with linked phone numbers and map directions
- "Your Next Steps" timeline with numbered action items

**Pause here** -- let the audience read the narrative for a moment.

---

### 6b. Benefits & Criminal Record Results (in plan view)

**Scroll to** benefits eligibility and expungement sections.

**Say:**
> "The system checks Texas benefits programs automatically -- SNAP, CHIP for his kid, CEAP for utility assistance, Texas TANF. The cliff chart shows what happens to net income as wages increase. See that drop around $15/hour? That's where SNAP phases out. We flag these cliffs so case workers can plan a wage trajectory that avoids them."

> "For the criminal record, it checked both pathways: Article 55 expunction AND Government Code Chapter 411 nondisclosure. With a misdemeanor theft and 3 years completed, he likely qualifies for nondisclosure -- sealing the record from most employer background checks. It shows the steps and connects to Legal Aid of NorthWest Texas."

**Highlight:**
- Texas-specific benefits programs (CHIP, CEAP, TX TANF)
- Benefits cliff chart with cliff points
- Nondisclosure eligibility (Texas-specific, dual pathway)

---

### 7. Barrier Cards + Job Matches (2:10 - 2:30)

**Scroll down** through the plan page.

**Say:**
> "Every barrier gets its own card with a timeline and specific action steps. Credit barrier -- 90-day repair plan. Transportation -- Trinity Metro routes mapped to his jobs. Each barrier card links to findhelp.org for discovering more local resources."

> "Jobs are ranked by Practical Value Score -- net income, transit proximity, schedule fit, and barrier compatibility combined. Fair-chance employers appear first. Each card shows the employer, transit route, and apply link."

**Highlight:**
- Barrier severity badges (high = red, medium = yellow)
- Fair-chance employer badges on job cards
- Transit route info on job cards
- PVS-ranked listings

---

### 8. Comparison + Export (2:30 - 3:00)

**Scroll to** "What Changes in 3 Months" section.

**Say:**
> "The comparison view shows Carlos today versus where he'll be in 3 months. Four barriers addressed, more jobs unlocked, credit improving. This is the motivation."

**Actions:**
1. Click "Download PDF" button
2. (PDF generates and downloads)
3. Point out "Email My Plan" button

**Say:**
> "He can download everything as a PDF to take to his case worker at Workforce Solutions, or email it to himself. This is the plan he walks in with Monday morning."

**Highlight:**
- Today vs In 3 Months side-by-side cards
- PDF download
- Share plan link for case worker

---

## Timing Summary

| Section | Duration | Cumulative |
|---------|----------|------------|
| Landing page | 15s | 0:15 |
| Basic Info | 15s | 0:30 |
| Barriers | 20s | 0:50 |
| Credit Check | 30s | 1:20 |
| Review & Submit | 20s | 1:40 |
| Plan -- Monday Morning | 30s | 2:10 |
| Barrier Cards + Jobs | 20s | 2:30 |
| Comparison + Export | 30s | 3:00 |

---

## Legacy Persona Reference (NOT for HackFW 2026 demos)

The Montgomery, AL deployment is preserved as the legacy reference city in the multi-city template architecture. It is NOT part of the HackFW 2026 wall narrative or live demo. The persona below is documented only so contributors maintaining the city-template layer have a regression reference.

For non-HackFW demos in Montgomery, set `CITY=montgomery`. For HackFW judges, this section can be ignored -- the live URL ships Fort Worth-only.

---

## Q&A Prep (2 minutes)

**Q: Is this a real credit check?**
> No. Self-reported assessment. No SSN, no hard pull. We match job credit requirements and estimate repair timelines.

**Q: Where do the jobs come from?**
> Fort Worth uses Texas Workforce Commission (TWC) and USAJobs APIs. Jobs refresh regularly. The architecture is city-agnostic, so other cities plug in via their own adapters.

**Q: How does the criminal record screening work?**
> State-specific. Texas checks both Article 55 expunction AND Government Code Chapter 411 nondisclosure (the dual-pathway system). We also match employer fair-chance policies. No legal advice -- we point to Legal Aid of NW Texas.

**Q: Could this work for other cities?**
> Yes. The architecture is city-agnostic. Each city is a YAML config + seed data. Swap the data for a new city and everything adapts: benefits programs, criminal record laws, transit, employer data, AI prompts.

**Q: What about data privacy?**
> No accounts, no PII stored permanently. Session data lives in SQLite during the session (30-day expiry). Credit data stays in the browser's sessionStorage only.

---

## Fallback Plan

If something breaks during the demo:

- **Backend down:** Frontend shows a friendly error. Refresh and retry. Have a backup video ready.
- **AI narrative fails:** Fallback narrative auto-generates (warm, city-specific, no API needed). Point this out as a resilience feature.
- **Credit API timeout:** Assessment continues without credit data. Plan still generates.
- **Job APIs unavailable:** Core job matches still show from seed data.
