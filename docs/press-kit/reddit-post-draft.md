# r/PairCoder Post Draft — Legacy MontGoWork Case Study

> **Status:** historical. This draft is for the LEGACY MontGoWork
> (Montgomery, AL) case study. The HackFW 2026 submission is GoWork
> (Fort Worth, TX) -- see `docs/press-kit.md` for the active narrative.

**Subreddit:** r/PairCoder
**Account:** macaulay_codin
**Type:** case study / use case

---

## Title Options (pick one)

1. hackathon project turned enforcement-driven civic tech. 1808 tests. built with paircoder.
2. we placed 2nd at a hackathon with 1808 tests. here's what enforcement-driven dev looks like on civic tech.
3. montgowork. workforce navigator for montgomery alabama. 1808 tests. built with paircoder.

---

## Post Body

built this with my co-dev, cohort and pahtnah shawn for the worldwide vibes hackathon. placed 2nd out of 2700 entrants. started as a hackathon project, turned into real enforcement-driven civic tech.

Here's the deets: montgowork is a workforce navigator for montgomery, alabama. residents dealing with employment barriers (criminal record, no car, no childcare, bad credit, housing, health, training) go through an assessment and get a personalized plan. jobs ranked by practical value score, benefits eligibility across 7 alabama programs, criminal record routing with expungement guidance, ai chat for barrier questions, and a printable package they take to the career center monday morning.

the system does the math that career center staff do manually every day. what happens to your SNAP if you take a $15/hr job. whether the bus gets you there by 7am. which employers actually hire people with records.

**the stack:**
- fastapi + next.js 15
- multi-provider llm (claude, openai, gemini with auto-fallback)
- faiss vector store + barrier graph for the ai chat
- brightdata + jsearch + honest jobs for job aggregation
- 1,391 backend tests (pytest), 417 frontend tests (vitest)

**built with paircoder.**
we ran the enforcement workflow the entire build. sprint planning, tdd gates, arch checks. every feature started as a failing test. the barrier graph has 33 nodes and 53 edges modeling how barriers cause each other. the benefits cliff detection calculates net income at every wage step. the expungement routing checks eligibility under alabama act 2021-507. none of that ships without deterministic test coverage first.

1808 tests isn't afterthought coverage. it's how the code got written.

repo: https://github.com/fivedollarfridays/montgowork

---

## Notes

- No CTA at the end
- No "what do you think" or "anyone else building civic tech"
- Links: GitHub repo (once public), screenshots can go in comments or as image post
- Consider posting screenshots as a gallery/image post instead of text, with the writeup in the first comment
- "built with paircoder" is a section header, not a throwaway line at the end
