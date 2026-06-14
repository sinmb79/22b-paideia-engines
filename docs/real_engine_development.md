# Real Engine Development Roadmap

[한국어](real_engine_development.ko.md)

This roadmap tracks the real development work needed to turn the Paideia engine suite from a scaffold into reusable engine assets.

## Current Position

The first development wave established the data acquisition and curriculum mapping foundations. Serious cultivation, assessment, stress, and promotion engines need trustworthy data and grade-subject-achievement mapping before they can become reliable.

Phase 2 strengthened assessment and cultivation. Phase 3 now strengthens stress rehearsal and promotion so they can be used as separate assets instead of being hidden inside the orchestration layer.

## Phase 1: Data And Curriculum

Added packages:

```text
src/paideia_engines/data_acquisition/
src/paideia_engines/curriculum_mapping/
examples/data_and_curriculum_pipeline.py
data/curriculum/sample_standards.json
```

Capabilities:

- License-gated source decisions
- Engine-specific acquisition plans
- Restricted textbook blocking
- Acquired source hashing
- JSONL manifest writing
- Learning unit generation from achievement standards
- Handoffs to cultivation, assessment, stress, and promotion engines

Example:

```powershell
python examples\data_and_curriculum_pipeline.py
```

## Phase 2: Assessment And Cultivation

Added:

```text
src/paideia_engines/assessment/item_bank.py
examples/assessment_and_cultivation_pipeline.py
```

Capabilities:

- Assessment item bank
- Gate construction
- Objective, short-answer, and solution-process item models
- Per-item rubric scoring
- Review-label candidate output
- Cultivation roadmap generation from learning units
- Assessment gates embedded in the roadmap

Example:

```powershell
python examples\assessment_and_cultivation_pipeline.py
```

## Phase 3: Stress And Promotion

Added:

```text
src/paideia_engines/stress/scenario_bank.py
examples/stress_and_promotion_pipeline.py
```

Capabilities:

- Stress scenario bank mapped to curriculum standards
- Scenario selection by standard and stressor type
- Stress plan generation for a standard
- Scenario execution with candidate-only promotion signals
- Trap-risk detection that blocks memory promotion pending review
- Versioned promotion ledger
- Quarantine reconsideration after verified review
- Promoted experience supersession without deleting history
- Active memory routing that excludes quarantined and superseded entries

Example:

```powershell
python examples\stress_and_promotion_pipeline.py
```

## Next Engine Development Order

1. Governance Engine v0.2: policy enforcement, approval records, and committee decision trails.
2. Runtime Engine v0.2: stronger traces, acceptance evidence, and replayable task records.
3. Orchestration v0.2: combine the upgraded engines without hiding their independent contracts.
4. Dataset adapters: legal, manifest-driven adapters for public curriculum and assessment data.

## Verification

```powershell
python -m pytest tests -q
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
```
