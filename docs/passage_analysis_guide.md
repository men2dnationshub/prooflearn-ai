# ProofLearn AI Passage Analysis Guide

## Purpose

Passage Analysis helps an educator locate internal changes in a longer
assignment. It compares each passage with the same document rather than assuming
that one universal writing style is normal.

## Segmentation

The engine preserves paragraph numbers. Short neighbouring paragraphs are
grouped into readable analysis passages. Very long paragraphs are divided at
sentence boundaries and identified by part number. Default passages target 50
to 180 words, and the document must contain at least 120 words.

## Comparison features

Each passage is compared with the complete document using:

- average sentence length
- sentence-length variation
- punctuation frequency
- repeated two-word phrase frequency

These differences produce a descriptive variation score and one of three labels:
Typical, Notable or Strong Variation.

## Interpretation

Variation can result from headings, quotations, edited sections, technical
explanations, copied source material, language proficiency, collaboration or a
natural change in the writer's approach. It is not proof of AI use or a change
of author.

An educator should use a flagged passage to ask a grounded question such as:

> In paragraphs four to five, your sentence structure changes. Can you explain
> the argument you developed there and how you wrote that section?

The downloadable JSON report preserves passage IDs, paragraph references,
metrics, observations, methodology and the required disclaimer.
