# Real Engine Development Roadmap

[한국어](real_engine_development.ko.md)

The first real development step is the data acquisition engine plus the curriculum mapping engine. Every serious cultivation, assessment, stress, and promotion engine needs trustworthy data and grade-subject-achievement mapping first.

## Added in v0.2

```text
src/paideia_engines/data_acquisition/
src/paideia_engines/curriculum_mapping/
examples/data_and_curriculum_pipeline.py
data/curriculum/sample_standards.json
```

## Data Acquisition Engine

Responsibilities:

- License-gated source decisions
- Engine-specific acquisition plans
- Restricted textbook blocking
- Acquired source hashing
- JSONL manifest writing

## Curriculum Mapping Engine

Responsibilities:

- Grade and subject learning units
- Achievement standard mapping
- Dataset coverage reports
- Handoffs to cultivation, assessment, stress, and promotion engines

## Phase 2 Progress

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

## Next Engine Development Order

1. Stress Engine v0.2
2. Promotion Engine v0.2
3. Governance Engine v0.2
4. Runtime/Orchestration v0.2

## Verification

```powershell
python -m pytest tests -q
python examples\data_and_curriculum_pipeline.py
```
