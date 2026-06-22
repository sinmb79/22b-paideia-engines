# Closed-Loop Curriculum Feedback Loop

Release target: 2026-Q3  
Codename: Adaptive Curriculum Feedback Loop

This update extends Paideia's pattern learning cycle from:

```text
Learning -> Exam -> Outcome -> Reinforcement
```

to:

```text
Outcome -> Weakness Detection -> Curriculum Generation -> Adaptive Exam -> Reinforcement Re-evaluation
```

## Added

- `paideia_engines.curriculum`
- `WeaknessRecord`
- `CurriculumPlan`
- `AdaptiveExam`
- Failure-to-weakness mapping
- Weakness-to-curriculum generation
- Adaptive exam generation
- Curriculum completion updates that reduce or increase weakness severity
- Kibo governance gates for high-severity or repeated weaknesses
- Pattern reinforcement caps when remediation is not complete

## Safety

- Local JSON/JSONL artifacts only.
- No external database dependency.
- Hidden chain-of-thought is not used.
- Repeated weaknesses block direct reuse.
- High-severity weaknesses require re-exam evidence before strong reuse resumes.

## Validation

- Full test suite: `271 passed`
