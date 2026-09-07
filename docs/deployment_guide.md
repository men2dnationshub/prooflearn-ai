# ProofLearn AI deployment guide

This guide publishes v0.12 as a **controlled demonstration prototype**. A successful deployment does not make its authorship outputs scientifically validated or suitable for disciplinary decisions.

## Before deployment

1. Run `python -m pytest -q`.
2. Run `python scripts/release_check.py`.
3. Run `python scripts/deployment_check.py`.
4. Confirm the final command reports `DEPLOYABLE_PROTOTYPE` and `production_ready: false`.
5. Use synthetic, public, or properly authorised test documents only.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and push this project so `app.py` and `requirements.txt` remain in the repository root.
2. Sign in to Streamlit Community Cloud and choose **Create app**.
3. Select the GitHub repository, the `main` branch, and `app.py` as the entry point.
4. In advanced settings, select Python 3.12.
5. No secrets are required for v0.12. If a future release uses an API key, store it in the platform's secret settings—never in Git.
6. Deploy and wait for dependency installation and application startup.

## Post-deployment smoke test

- Home page loads and shows version 0.12.0.
- Assignment Review accepts a safe TXT, DOCX, and PDF sample.
- Writing statistics and passage indicators render.
- Dataset Lab validates a sample dataset and can train the experimental baseline when both classes are present.
- Proof of Learning generates document-grounded questions.
- Writing Assistant produces suggestions and an AI-assistance declaration.
- Reports exports the expected evidence.
- No student document remains after the browser session is cleared or the app restarts.

## Known hosting constraints

- Session state is temporary. In-session models, uploaded documents, reviews, and reports can disappear when the app restarts.
- The package intentionally includes no trained production classifier or private student corpus.
- Community-hosted demos are not approved for confidential student records.
- Resource limits make this deployment appropriate for demonstrations and small controlled tests, not institutional workloads.

## Rollback

Revert the problematic Git commit, push the corrected `main` branch, and redeploy. Record the deployed commit identifier before each pilot session.

## Official deployment references

- Streamlit Community Cloud deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Dependency management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- Secret management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
