# Curriculum Mapping Engine

[한국어](README.ko.md)

The Curriculum Mapping Engine turns achievement standards into reusable learning units.

## Owns

- `CurriculumStandard` normalization
- Grade, subject, and school-level learning units
- Dataset coverage reports
- Engine handoff metadata

## Public API

- `CurriculumMappingEngine(standards)`
- `build_learning_unit(...)`
- `coverage_report(dataset_sources)`

## Safety Boundary

This engine maps standards. It does not score learner work or promote memory.
