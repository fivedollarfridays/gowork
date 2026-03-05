# MontGoWork Demo Script

> 3-minute live demo + 2-minute Q&A. Presenter walks through the Maria persona end-to-end.

---

## Pre-Demo Checklist

- [ ] Backend running: `cd backend && uvicorn app.main:app --reload` (port 8000)
- [ ] Frontend running: `cd frontend && npm run dev` (port 3000)
- [ ] `ANTHROPIC_API_KEY` set in `backend/.env` (for AI narrative)
- [ ] Seed data loaded: `cd backend && python -m app.seed` (resources + employers)
- [ ] BrightData API key set (optional -- live jobs section only shows if crawled data exists)
- [ ] Browser at `http://localhost:3000`, zoomed to 125% for visibility
- [ ] Screen sharing active, dark/light mode matches projector

---

## Maria Persona

| Field | Value |
|-------|-------|
| Name | Maria |
| Age | 34 |
| Location | Montgomery, AL (ZIP 36104) |
| Situation | Recently released, single mother of 2 |
| Vehicle | No |
| Employment | Unemployed |
| Work history | 3 years retail and food service before incarceration |
| Credit score | ~580 (Very Poor) |
| Utilization | 65% |
| Payment history | 75% on-time |
| Account age | 1-3 years |
| Accounts | 4 total, 2 open, 1 in collections |
| Negative items | Late payments, collections |
| Barriers | Credit, Transportation, Childcare, Criminal Record |

---

## Demo Flow (3 minutes)

### 1. Landing Page (0:00 - 0:15)

**URL:** `http://localhost:3000`

**Click:** "Get Your Plan" button (hero section)

**Say:**
> "Meet Maria. She's 34, lives in Montgomery, just came home from incarceration. Two kids, no car, credit score around 580. She's got barriers -- but she's ready to work. Let's see what MontGoWork does for her."

**Highlight:** The three-step flow cards (Assess, Match, Plan) and Montgomery stats.

---

### 2. Basic Info -- Step 1 (0:15 - 0:30)

**Page:** `/assess` -- Step 1 of wizard

**Actions:**
1. Type `36104` in ZIP Code field
2. Select "Unemployed" from Employment dropdown (already default)
3. Leave "I have a vehicle" unchecked
4. Click "Next"

**Say:**
> "ZIP code 36104 -- downtown Montgomery. Unemployed, no vehicle. That already tells us a lot about what resources she'll need."

**Highlight:** ZIP validation (only accepts Montgomery-area 361xx codes).

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
> "Four barriers. Credit history, no car, needs childcare, and a criminal record. Notice the severity badge -- it updates live. Four barriers puts her in 'high' severity. The system will prioritize resources for her most critical needs."

**Highlight:** Severity badge changing as barriers are selected. Cards highlight with checkmarks.

---

### 4. Credit Check -- Step 3 (0:50 - 1:20)

**Page:** `/assess` -- Step 3 (only appears because credit barrier was selected)

**Actions:**
1. Drag credit score slider to **580** (should show "Very Poor" in red)
2. Drag utilization slider to **65%** (shows red -- above 30% threshold)
3. Drag payment history to **75%**
4. Select "1-3 years" from account age dropdown
5. Enter **4** total accounts, **2** open, **1** in collections
6. Check "Late Payments" and "Collections" under negative items
7. Click "Next"

**Say:**
> "This is the credit self-assessment. No hard pull -- Maria enters what she knows. Score of 580, high utilization, some late payments and a collections account. The system will use this to figure out which employers she can apply to right now, and which ones she'll qualify for after credit repair."

**Highlight:** The color-coded score band (Very Poor = red), utilization turning red above 30%.

---

### 5. Review & Submit -- Step 4 (1:20 - 1:40)

**Page:** `/assess` -- Step 4 of wizard

**Actions:**
1. Type in Work History: `3 years retail at Dollar General. Food service at Popeyes. Forklift certified.`
2. Review the summary card (ZIP, Employment, Barriers, Vehicle, Credit Score)
3. Click "Submit Assessment"

**Say:**
> "She adds her work history -- retail and food service, plus a forklift cert. That opens up warehouse jobs. The summary shows everything at a glance. When she submits, the backend scores her profile, runs matching filters, builds her plan, and kicks off the AI narrative -- all in one request."

**Highlight:** The summary card with all her data. The loading spinner with "Analyzing your profile and matching resources..."

---

### 6. Plan View -- Monday Morning (1:40 - 2:10)

**Page:** `/plan?session=<id>` -- auto-redirected after submit

**Say:**
> "Here's the magic. 'What you can do Monday morning.' The AI writes a personalized narrative -- not generic advice, but Montgomery-specific. It knows about M-Transit routes, the Alabama Career Center on Ripley Street, GreenPath Financial for credit counseling. Every action step has a phone number, address, or link."

**Highlight:**
- AI narrative card with sparkle icon (may show loading spinner briefly)
- "Key Actions" cards with linked phone numbers and map directions
- "Your Next Steps" timeline with numbered action items

**Pause here** -- let the audience read the narrative for a moment.

---

### 7. Barrier Cards + Job Matches (2:10 - 2:30)

**Scroll down** through the plan page.

**Say:**
> "Below the narrative, every barrier gets its own card with a timeline and specific action steps. Credit barrier -- 90-day repair plan. Transportation -- M-Transit routes mapped to her jobs and resources."

> "Job matches are split: 'Qualified Now' are jobs with no credit check -- warehouse, food service. 'After Credit Repair' shows what opens up once she hits a 650 score. Each card shows the employer, transit route, and apply link."

**Highlight:**
- Barrier severity badges (high = red, medium = yellow)
- "Qualified Now" vs "After Credit Repair" job sections
- Transit route tags on job cards

---

### 8. Comparison + Export (2:30 - 3:00)

**Scroll to** "What Changes in 3 Months" section.

**Say:**
> "The comparison view shows Maria today versus where she'll be in 3 months. Four barriers addressed, more jobs unlocked, credit improving. This is the motivation."

**Actions:**
1. Click "Download PDF" button
2. (PDF generates and downloads)
3. Point out "Email My Plan" button

**Say:**
> "She can download everything as a PDF to take to her case worker, or email it to herself. This is the plan she walks into the Alabama Career Center with on Monday morning."

**Highlight:**
- Today vs In 3 Months side-by-side cards
- PDF download (show the generated file briefly if time permits)

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

## Q&A Prep (2 minutes)

**Likely questions and answers:**

**Q: Is this a real credit check?**
> No. It's a self-reported assessment. No SSN, no hard pull. We use the data to match job credit requirements and estimate a repair timeline.

**Q: Where do the jobs come from?**
> Two sources. Seed data from Montgomery employer partnerships, and live scraping from Indeed/LinkedIn via BrightData. Jobs refresh every 24 hours.

**Q: How does the AI narrative work?**
> We send the plan data to Claude with a Montgomery-specific persona prompt. It writes like a career counselor at the Alabama Career Center -- warm, specific, actionable. If the API is down, a handwritten fallback kicks in.

**Q: What about data privacy?**
> No accounts, no PII stored permanently. Session data lives in SQLite during the session and can be cleared. Credit data stays in the browser's sessionStorage only.

**Q: Could this work for other cities?**
> The architecture is city-agnostic. Resources, transit routes, and employer data are all in the database. Swap the seed data and prompts for a new city.

---

## Fallback Plan

If something breaks during the demo:

- **Backend down:** The frontend will show a friendly error. Refresh and retry. Have a backup video recording ready.
- **AI narrative fails:** The fallback narrative auto-generates (warm, Montgomery-specific, no API needed). Point this out as a resilience feature.
- **Credit API timeout:** Assessment continues without credit data. Plan still generates with barrier-based matching.
- **BrightData not configured:** "Explore More Jobs" section simply doesn't appear. Core job matches still show from seed data.
