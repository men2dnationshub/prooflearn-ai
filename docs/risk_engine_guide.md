# ProofLearn AI Explainable Risk Engine

## Purpose

The risk engine converts validated model evidence into a review priority. It does
not determine authorship or misconduct. Its primary safety feature is the ability
to abstain and return `INSUFFICIENT_EVIDENCE`.

## Evidence gates

The experimental policy refuses to score when any of these conditions applies:

- the assignment contains fewer than 150 words
- the independent evaluation set contains fewer than 30 records
- model macro F1 is below 60%
- the model incorrectly flags more than 15% of HUMAN evaluation samples
- the difference between the two highest class probabilities is below 10%

These defaults are policy hypotheses for prototype testing. They are not
scientifically validated thresholds and must be revisited using real evidence.

## Score composition

When all evidence gates pass, the experimental score combines:

| Component | Weight |
| --- | ---: |
| Model probability for AI or AI_ASSISTED | 80% |
| Transparent structural writing patterns | 20% |

The writing component uses only capped sentence-length consistency, repeated
two-word phrases and repeated sentence openings. This component is deliberately
small because these patterns can occur in legitimate human writing.

## Outcomes

| Outcome | Meaning | Action |
| --- | --- | --- |
| LOW | Limited review signal | Continue normal academic review |
| MODERATE | Some indicators warrant review | Verify selected claims and methods |
| HIGH | Stronger review priority | Conduct student verification promptly |
| INSUFFICIENT_EVIDENCE | A safeguard failed | Do not issue a risk level |

No outcome should trigger an automatic penalty. Reports retain the policy
version, safeguards, component weights, observations and recommended action so
that the result can be audited.
