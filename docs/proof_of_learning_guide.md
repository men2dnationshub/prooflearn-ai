# ProofLearn AI Proof of Learning Guide

## Purpose

Proof of Learning shifts the review from guessing who wrote a document to
observing whether the student understands and can explain the submitted work.

## Grounded question generation

The Milestone 8 engine works locally without an external AI service. It selects
complete sentences from the assignment and generates up to six question types:

| Type | What it checks |
| --- | --- |
| Knowledge | Meaning of an important term in context |
| Understanding | Explanation of a submitted point in the student's own words |
| Method | Ability to reproduce a process, calculation or evidence path |
| Reasoning | Connection between evidence and a claim |
| Application | Ability to adapt the idea when a condition changes |
| Critique | Recognition of limitations or alternative explanations |

Every question displays its paragraph and sentence reference plus a short source
excerpt. This allows the educator and student to see exactly what prompted it.

## Rating scale

| Score | Meaning |
| ---: | --- |
| 0 | Unable to explain |
| 1 | Partial understanding |
| 2 | Adequate understanding |
| 3 | Strong understanding |

Missing ratings remain Not Assessed. ProofLearn will not silently convert them
to zero or calculate a final score until all generated questions are rated.

## Interpretation

The Learning Verification Score records demonstrated understanding during a
review conversation or practical defence. It does not prove whether AI was used.
A low score may also reflect anxiety, language barriers, accessibility needs,
poor questioning conditions or gaps in instruction. Educators should record
evidence, provide reasonable support and follow institutional policy.
