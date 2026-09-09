# ProofLearn AI

**Verify Authorship. Validate Learning. Improve Writing.**

ProofLearn AI is an education focused application that will help educators
identify authorship concerns, inspect explainable writing indicators and verify
whether students understand submitted work.

## Version 0.13 status

ProofLearn AI v0.13 is a post-deployment polish release. It adds named Home navigation, stronger dashboard and sidebar branding, a fictional sample assignment, prominent privacy guidance, and clearer empty-state instructions.

Passing the deployment gate means the software can be demonstrated. It does **not** mean the detector is scientifically validated or approved for production decisions.

The Responsible Writing Assistant is complete. ProofLearn now includes:

- controlled clarity, conciseness, grammar, flow and tone goals
- side by side original and suggested text
- itemised and explained changes
- before and after word and readability metrics
- downloadable revised text and change record
- an AI assistance declaration
- no detector bypass or concealment mode

Run `streamlit run app.py` and use the sidebar navigation.

## Run locally

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
streamlit run app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Run tests

```bash
pytest -q
```

## Responsible use

ProofLearn AI will report authorship review risk rather than claim conclusive AI
authorship. Educators should combine indicators with student verification and
institutional policy before making academic decisions.

## Current limitations

- Legacy `.doc` files are not supported. Save them as `.docx` first.
- Image-only and scanned PDFs need OCR, planned for a later enhancement.
- Password protected files must be unlocked before upload.
- Readability syllables are estimated and work best for English prose.
- Short samples can produce unstable vocabulary and repetition ratios.
- Passive voice detection is an indicator, not a full grammar parser.
- Basic personal-information screening does not replace human anonymisation.
- A meaningful classifier requires a large, diverse and carefully documented corpus.
- Raw class probabilities are not calibrated institutional risk scores.
- Performance on one test dataset does not establish general reliability.
- Risk weights and thresholds remain experimental policy hypotheses.
- Linguistic patterns may reflect language background, disability or writing instruction.
- Paragraph references depend on the structure preserved during file extraction.
- Very short passages are grouped and may span more than one source paragraph.
- Generated questions are starting prompts and still require educator judgement.
- Oral performance may be affected by language, anxiety and accessibility needs.

## Deployment

Run these gates before publishing:

```bash
python scripts/release_check.py
python scripts/deployment_check.py
```

Then follow [docs/deployment_guide.md](docs/deployment_guide.md). Operational and pilot safeguards are in [docs/operations_runbook.md](docs/operations_runbook.md).

## Roadmap complete

Milestones 1–12 are implemented for the ProofLearn AI V0.1 prototype roadmap. The next phase is evidence gathering: authorised corpus creation, independent model validation, privacy and accessibility review, and a supervised educator pilot.
