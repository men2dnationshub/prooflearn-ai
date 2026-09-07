# Milestone 10 Validation and Release Readiness

## Outcome

ProofLearn AI is a validated prototype, not a production academic decision
system. Automated checks cover document extraction, text features, dataset
governance, baseline modelling, risk abstention, passage analysis, grounded
questions, scoring, multipage startup and an end to end assignment workflow.

## Privacy and security checks

- uploaded assignments are processed in memory
- `.env` and model files are excluded from source packages
- DOCX archive size and compression ratio are checked before parsing
- dataset validation warns about possible emails and phone numbers
- model deserialisation is restricted to trusted local files
- clearing an assignment removes document-specific reports from session state

## Accessibility review checklist

- every interactive input has a visible label
- status is communicated with text, not colour alone
- headings follow a clear page hierarchy
- tables retain written column labels
- warnings and disclaimers use plain language
- keyboard navigation and screen-reader behaviour require manual browser testing
- colour contrast and mobile layout require manual testing before pilot release

## Failure modes covered

Empty, damaged, oversized, password-protected and unsupported documents; scanned
PDFs without OCR; very short text; duplicate or unlicensed training data; author
leakage; missing model classes; weak evaluation evidence; uncertain predictions;
incomplete verification ratings; invalid risk policies; and empty application
states.

## Production blockers

1. No representative authorised training corpus is bundled.
2. No independently validated production model is approved.
3. Institutional privacy, accessibility and academic-integrity review is pending.
4. A real educator pilot has not been completed.

Run `python scripts/release_check.py` and `pytest -q` before every packaged release.
