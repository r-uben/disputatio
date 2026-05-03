# Outreach prep

Working artifacts for the first round of professor outreach. Status: drafts ready for user review; nothing sent yet.

## What's here

| File | Purpose |
|---|---|
| [`../pitch.md`](../pitch.md) | One-page description of disputatio. Doubles as email attachment + website "About" page. |
| [`email_template.md`](email_template.md) | First-contact email + follow-up template. Variables for per-recipient customization. |
| [`feedback_form.md`](feedback_form.md) | 5-question form spec for Google Form / Typeform. |
| [`website_bench_post.md`](website_bench_post.md) | Long-form bench writeup (coarse comparison + drop-mini + v8.0 design + Galeotti J). For the gh-pages site. |

## Strategy (per codex 5.5 sess 135)

**Q1 framing**: lead with pain, not architecture. Architecture is one click deeper.

**Q2 demo**: ship now with Galeotti panel, labeled clearly as a published-paper worked example. Queue a fresh-paper run as v2 outreach material.

**Q3 list**: 3–5 hand-picked recipients, social graph not cold. User to propose 5–8 candidates; we workshop down.

**Q4 limitations**: visible "what this does not claim" section in pitch + one-sentence honest caveat in email body.

**Q5 reduced ask**: first email asks for 10 min of feedback on the demo panel, NOT for the recipient's draft. Only after positive reply do we offer to run on their work.

## What's blocking sending the first email

1. **Demo panel link**: Galeotti panel exists in the Obsidian vault. Needs to be published somewhere link-able — ideally as a static page on the gh-pages site. Until then we can paste the panel.md inline as an attachment, but a hosted link is much better.
2. **Feedback form link**: needs the actual Google Form / Typeform created. The spec in `feedback_form.md` is ready; user creates the form.
3. **Recipient list**: user needs to propose 5–8 candidates with field anchors per codex's discovery process.
4. **Sender identity**: the email template's `{sender_name}` and the affiliation context block need to be filled.

## What the user does next

1. **Review the four artifacts** in this directory — sharp edits welcome on the pitch (especially the "what this does not claim" section), the email tone, and the bench post framing.
2. **Create the Google Form** from `feedback_form.md` spec.
3. **Publish the Galeotti panel** to a static location (gh-pages, gist, or anywhere link-able).
4. **List 5–8 candidate recipients** with one-line per-recipient anchor.
5. **Send to first 3** in Round 1. Wait a week before Round 2.

## What we don't do in Round 1

- Send to anyone publicly hostile to LLM tooling.
- Send to a full professor whose canonical work the demo paper is in the same area as — looks insulting.
- Send without the demo link being live.
- Promise a fresh-paper run we haven't yet done.
- Aggregate or quote feedback for marketing without explicit permission from the respondent.
