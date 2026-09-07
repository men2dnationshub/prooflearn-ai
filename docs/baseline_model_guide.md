# ProofLearn AI Baseline Model Guide

## What Milestone 5 provides

The baseline combines word and character TF IDF features with multinomial
Logistic Regression. It predicts HUMAN, AI_ASSISTED or AI and produces class
probabilities. The model is intentionally interpretable and reproducible enough
to establish a benchmark before more complex methods are considered.

## Required evidence

Every experiment reports accuracy, macro F1, per-class precision, recall and F1,
the confusion matrix, the rate at which HUMAN samples are incorrectly flagged,
and the rate at which AI or AI_ASSISTED samples are incorrectly classified as
HUMAN. Accuracy alone is not an acceptable release criterion.

## Leakage controls

Dataset validation runs before training. Exact duplicates and authors appearing
across multiple splits block training. The classifier learns only from records
assigned to `train` and evaluates on the independently assigned `test` split by
default.

## Model lifecycle

Each saved model bundle contains its pipeline, dataset fingerprint, training
timestamp, package version, labels, evaluation report and a false
`production_approved` flag. A model must not become production approved merely
because it trained successfully.

Joblib model files must only be loaded from a trusted internal path. They must
never be accepted as arbitrary user uploads because deserialising an untrusted
model file can execute malicious code.

## Release gate

Before educator use, evaluate the model on unseen writing across subjects,
education levels, language backgrounds, writing abilities and AI systems. Set a
strict acceptable human false-positive threshold, document uncertainty, conduct
educator review, and retain student verification as the decision process.
