# Outreach email template — first contact

**Strategy**:

- Reduced ask: 10 minutes of feedback on a description-only site + (optionally) a worked panel as attachment. NOT "send me your paper" yet.
- Lead with pain, not architecture.
- Headline framing: disputatio produces a *folder of audit material* the author uses to revise — not a finished referee report.
- Confidentiality disclosure goes in the *follow-up* email (when the author offers their own paper), not the first contact.
- Variables: `{first_name}`, `{paper_or_topic_anchor}` (recipient-specific anchor — recent paper they wrote, topic they're known for, course they teach), `{site_link}` (https://rubenfernandezfuertes.com/disputatio-ccc1a3e8/), `{sender_name}`.

---

## Email

**Subject**: quick feedback on a pre-submission paper audit tool?

> Hi {first_name},
>
> Before submission, one of the hardest problems is knowing which serious referee objection you have not yet anticipated. I have been building **Disputatio**, a tool that audits economics papers across three model families (Claude / GPT / Gemini) and produces a folder of inspectable audit material — finding panel, drop trail, debate transcripts — that the author reads through and uses as source material when revising.
>
> Given your work on {paper_or_topic_anchor}, I thought you might have a useful eye for whether this kind of output is actually valuable to authors. There is a short description of the system at {site_link}. If you want a concrete artifact, I can also send the panel I ran on Galeotti, Golub & Goyal (2020, *Econometrica*) as an attachment — published paper, so it shows the format and critique level rather than a "before submission" demo.
>
> Would you be willing to spend 10 minutes looking at it and telling me whether the findings seem useful, wrong, or irrelevant? I am not asking you to send a paper at this stage.
>
> The honest caveat is that this is early: it is not a referee substitute, not broadly validated yet, and runs are slow. I would mainly value your judgment on whether the direction is worth pursuing.
>
> Best,
> {sender_name}

---

## Follow-up after positive response

If the recipient replies with substantive feedback or asks "can you run it on my X":

> Thanks {first_name} — really helpful.
>
> If you'd be open to it, I can run disputatio on a draft you authored and send back the full audit folder: finding panel, drop trail with reasons, calibration annotations, and a short referee-style memo you can edit in your own voice. The run takes ~2.5 hours on my side, no rush on yours.
>
> One honest disclosure on confidentiality: files are handled locally on my machine, but during inference the paper text is sent to Anthropic, OpenAI, and Google through my paid subscriptions. This is not a confidential channel. Only send work you would be comfortable having processed by those providers under their data-handling terms. If this would be referee work on someone else's manuscript, check your journal policy first — most journals prohibit it.
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
- The site link in the email is broken or unreachable — verify it loads cleanly before sending.
