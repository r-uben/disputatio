# Outreach email template — first contact

**Strategy** (per codex 5.5 sess 135 review):

- Reduced ask: 10 minutes of feedback on a demo panel, NOT "send me your paper" yet.
- Lead with pain, not architecture.
- Demo is a worked example on a published paper (Galeotti), labeled clearly as such — not oversold as a fresh submission.
- One honest-caveat sentence in the body.
- Variables: `{first_name}`, `{paper_or_topic_anchor}` (recipient-specific anchor — recent paper they wrote, topic they're known for, course they teach), `{demo_panel_link}`, `{sender_name}`.

---

## Email

**Subject**: quick feedback on a pre-submission paper audit tool?

> Hi {first_name},
>
> Before submission, one of the hardest problems is knowing which serious referee objection you have not yet anticipated. I have been building **Disputatio**, a tool that audits economics papers across three model families (Claude / GPT / Gemini) and returns a structured finding panel rather than generic prose feedback.
>
> Given your work on {paper_or_topic_anchor}, I thought you might have a useful eye for whether this kind of output is actually valuable to authors. Here is a worked demo panel: {demo_panel_link}. It is run on an existing economics paper (Galeotti, Golub & Goyal 2020 in *Econometrica*), so it is not presented as "before submission," but as an example of the current output format and level of critique.
>
> Would you be willing to spend 10 minutes looking at the demo and telling me whether the findings seem useful, wrong, or irrelevant? I am not asking you to send a paper at this stage.
>
> The honest caveat is that this is early: it is not a referee substitute, not broadly benchmarked yet, and runs are still slow. I would mainly value your judgment on whether the direction is worth pursuing.
>
> Best,
> {sender_name}

---

## Follow-up after positive response

If the recipient replies with substantive feedback or asks "can you run it on my X":

> Thanks {first_name} — really helpful.
>
> If you'd be open to it, I can run disputatio on a draft you have near submission and send back the panel + a short referee-style memo. The run takes a couple of hours on my side, so no rush on your end. Caveat: anything you send stays on my local machine; the LLM calls go through my own paid subscriptions, not via your account or institutional credentials.
>
> {sender_name}

---

## Workshop notes (per recipient)

Before sending, replace each `{}` variable. Tailor `{paper_or_topic_anchor}` per recipient — generic "your work on networks" is worse than "your 2024 *Targeting Interventions* extension."

If there is no warm context (the recipient does not know the sender), add a one-line intro before the body:

> We have not met — I am {sender_name}, {short context: PhD student at Bocconi / postdoc at Oxford / etc.}.

If there is warm context (introduced through a third party), open with that:

> {introducer_name} suggested I get in touch about a tool I have been building.

## When NOT to send

- The recipient has publicly criticized LLM tooling for academic work — find someone else.
- The recipient is a full professor who has written the canonical text on the relevant topic — they will not value LLM critique on their own work.
- The recipient and sender have no plausible field connection — looks like cold-spam.
- We do not yet have the demo panel link and feedback form ready — do not send the email; the demo is the artifact.
