# ProofLearn AI prototype operations runbook

## Intended use

ProofLearn AI v0.13 may be used for demonstrations and controlled, consented evaluation. It must not autonomously accuse, grade, penalise, or make an academic-misconduct determination.

## Start-up checks

- Confirm the deployed version and Git commit.
- Run the automated deployment check before publishing.
- Confirm no `.env`, `.streamlit/secrets.toml`, student documents, or trained model artifacts are committed.
- Use a synthetic sample to verify extraction, analysis, questions, writing suggestions, and reports.

## During a pilot

- Tell participants that outputs are experimental review signals.
- Obtain appropriate authorisation before processing student work.
- Minimise identifying information and avoid confidential submissions on public demo hosting.
- Require human review and let students explain their work.
- Record false positives, extraction failures, accessibility problems, and user feedback.

## Incident response

If confidential data, credentials, or unsafe output is exposed:

1. Stop the pilot and restrict access to the app.
2. Remove the exposed material from the repository and deployment settings.
3. Rotate any affected credentials.
4. Follow the institution's privacy and incident-reporting process.
5. Document the incident and verify the correction before redeployment.

If the app is unavailable, inspect deployment logs, reproduce locally with the same commit and pinned dependencies, and roll back if the issue cannot be corrected promptly.

## Pilot exit criteria

Do not advance toward production until the dataset provenance, subgroup evaluation, false-positive thresholds, privacy assessment, accessibility review, educator pilot, student appeal process, retention policy, and institutional approval are documented.
