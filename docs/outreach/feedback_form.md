# Disputatio feedback form spec

**Status: deferred to Round 2.** For Round 1 (3–5 hand-picked recipients) we use free-text email replies — richer signal at small n, lower friction for the recipient, no broken-form risk. This spec stays in the repo so when Round 2 scales the response count, the form is ready to build.

Five questions. Designed for a Google Form or Typeform. Total time target: ~5 minutes.

---

## Form intro (form header)

> Thanks for taking a look at the demo panel. Five quick questions on what you saw — your honest read matters more than polite praise. Free-text answers can be one sentence each.

---

## Question 1

**Which finding, if any, seemed most useful or closest to real referee feedback?**

- Field type: free text (long-form)
- Required: yes
- Help text: "Quote the finding ID (e.g. F003) or paraphrase the concern. If none, say so."

## Question 2

**Which finding, if any, seemed wrong, overstated, or unhelpful?**

- Field type: free text (long-form)
- Required: yes
- Help text: "We expect there will be some — this is the most useful answer."

## Question 3

**Would you consider using this on a draft before submission?**

- Field type: multiple choice
- Options: `Yes` / `Maybe` / `No`
- Required: yes

## Question 4

**How valuable would this be if the findings were reliably calibrated?**

- Field type: 1–5 scale
- Labels: `1 = not useful` / `5 = would change my workflow`
- Required: yes

## Question 5

**Optional: what kind of paper should we test next?**

- Field type: free text (short)
- Required: no
- Help text: "A specific working paper or a topic / venue we should target."

---

## Optional fields (for follow-up)

- Email (optional, for sending v2 follow-up only)
- Field/subfield (optional, for cohort analysis)

## What we do with responses

- Q2 (wrong/overstated findings) feeds the calibration audit log directly. Patterns there guide v8.x rubric tuning.
- Q3 + Q4 give a coarse "would-use" signal across recipients. Target: ≥3 of 5 say `Yes` or `Maybe` AND median Q4 ≥ 4.
- Q5 surfaces papers/venues for v2 outreach.
- Q1 is the positive-signal anchor — used in pitch material if multiple recipients agree.

## What we do NOT do

- Aggregate quotes from named recipients without explicit permission.
- Use responses for marketing without checking with the respondent first.
- Require email or identifying info to submit.
