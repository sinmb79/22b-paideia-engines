# Assessment Engine

[한국어](README.ko.md)

The Assessment Engine evaluates outputs with deterministic rubrics and item banks.

## Owns

- Rubric evaluation
- Assessment transcripts
- Item bank scoring
- Review-label candidate output

## Public API

- `AssessmentEngine(item_bank=None)`
- `evaluate(gate_id, submission)`
- `build_transcript(learner_id, results)`
- `evaluate_item_response(item_id, response)`
- `AssessmentItem`
- `ItemBank`

## Safety Boundary

This engine can produce review-label candidates. It does not promote memory directly.
