# Outreach prep

Working artifacts for the first round of professor outreach. Status: drafts ready, website live, nothing sent yet.

## What's here

| File | Purpose |
|---|---|
| [`../pitch.md`](../pitch.md) | One-page description of disputatio. Email attachment for recipients who want detail beyond the site. |
| [`email_template.md`](email_template.md) | First-contact email + follow-up template. Variables for per-recipient customization. |
| [`feedback_form.md`](feedback_form.md) | 5-question form spec. **Round 2 material** — for Round 1 we use email replies, not a form (n=3-5 is too small for structured aggregation). |

## Strategy

- **Frame**: disputatio produces a *folder of audit material* (panel + drop trail + calibration + memo) the author uses to revise. Not a finished referee report. The human writes that.
- **Demo**: the site (https://rubenfernandezfuertes.com/disputatio-ccc1a3e8/) is the primary artifact. For recipients who want a concrete panel example, attach the Galeotti panel — labeled as a published-paper worked example, not a fresh-submission demo.
- **Ask**: 10 minutes on the site + (optionally) the attached panel; reply by email with reactions. Not "send me your paper."
- **Recipients**: 3–5 hand-picked for Round 1, social graph not cold. Propose 5–8 candidates and workshop down.
- **Limitations**: site has a visible "what this does not claim" section; pitch and email body carry the same honest caveat.
- **Confidentiality**: disclosure language explicit in pitch.md and in the follow-up email (when offering to run on their paper). Author mode is primary; referee work only if journal policy permits.

## What's blocking sending the first email

1. **Recipient list**: 5–8 candidates with one-line per-recipient anchor (recent paper, topic, course they teach, social-graph link).
2. **Sender identity**: the email template's `{sender_name}` and the cold/warm intro variant.
3. **Optional: repo flip**. Path B on the site says "code available on request." If you want it to be a live GitHub link before Round 1, run `gh repo edit r-uben/disputatio --visibility public` and swap the site copy.

## What the user does next

1. **Reread** the artifacts in this directory and `../pitch.md` for tone / consistency with the website.
2. **List 5–8 candidate recipients** with one-line per-recipient anchor.
3. **Send to first 3** in Round 1. Wait a week before Round 2.

## What we don't do in Round 1

- Send to anyone publicly hostile to LLM tooling.
- Send to a full professor whose canonical work the demo paper is in the same area as — looks insulting.
- Send without verifying the site link loads cleanly.
- Promise a fresh-paper run we haven't yet done.
- Aggregate or quote feedback for marketing without explicit permission from the respondent.
