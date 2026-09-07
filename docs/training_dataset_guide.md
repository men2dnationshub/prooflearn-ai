# ProofLearn AI Training Dataset Guide

## Purpose

The training dataset will support later comparison of HUMAN, AI and AI_ASSISTED
writing. Milestone 4 creates the controlled data structure and quality checks. It
does not train or claim the accuracy of a classifier.

## Labels

| Label | Meaning |
| --- | --- |
| HUMAN | Written by a person without generative text assistance |
| AI | Generated primarily by a documented AI model |
| AI_ASSISTED | Human writing materially revised or extended with AI assistance |

Do not infer a label from writing style. Each label needs known provenance.

## Collection rules

1. Obtain explicit permission before using student work.
2. Remove names, emails, phone numbers, student IDs and other identifiers.
3. Use a pseudonymous `author_group_id` to keep one author's work together.
4. Record the source, consent or licence basis, and collection date.
5. For AI text, record the model and a prompt ID linked to a separate prompt log.
6. For AI assisted text, document the editing level and model where known.
7. Keep all texts from one author in only one of train, validation or test.
8. Never use private student assignments collected for grading without consent.

## Split strategy

A starting target is 70% training, 15% validation and 15% testing. Split by
`author_group_id`, not individual document, to reduce authorship leakage. Preserve
representation across labels, subjects, education levels and writing abilities.

## Required columns

| Column | Description |
| --- | --- |
| record_id | Unique record identifier |
| text | Anonymised writing sample |
| label | HUMAN, AI or AI_ASSISTED |
| source_type | Approved provenance category |
| source_reference | Internal source or collection batch reference |
| subject | Writing subject or discipline |
| education_level | Learner or writing level |
| language | Primary language of the sample |
| author_group_id | Pseudonymous author grouping for leakage control |
| model_name | AI model used, where applicable |
| generation_prompt_id | Reference to the prompt log |
| editing_level | none, light, moderate, substantial or unknown |
| consent_status | consented, licensed or not_applicable |
| license_or_permission | Evidence or policy reference |
| collection_date | ISO date in YYYY-MM-DD form |
| split | train, validation, test or unassigned |
| exclude_from_training | TRUE or FALSE |
| notes | Non-identifying context and quality notes |

The preparation pipeline adds text fingerprints, word counts and character
counts. Exact duplicate text, invalid labels, missing permission, and author
leakage across splits block preparation.

## Minimum viable collection target

Do not train a production detector from a tiny demonstration dataset. Begin with
a pilot corpus for pipeline testing, then expand to thousands of documented
samples across each class before drawing performance conclusions. The final
sample target must be decided from learning curves and subgroup evaluation.
