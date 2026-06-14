# Architecture

[한국어](architecture.ko.md)

Paideia Engines is organized around engine boundaries rather than a single agent loop. Each engine owns one kind of decision and emits deterministic records that other engines can consume.

```mermaid
flowchart TD
  Config["Config JSON"] --> Runner["Config Runner"]
  CLI["CLI"] --> Runner
  Runner --> DA["Data Acquisition"]
  DA --> CM["Curriculum Mapping"]
  CM --> C["Cultivation"]
  C --> AS["Assessment"]
  AS --> S["Stress"]
  S --> PS["Promotion Signal"]
  PS --> P["Promotion"]
  Runner --> G["Governance"]
  G --> R["Runtime"]
  R --> AM["Artifact Manifest"]
  R --> RT["Replayable Trace"]
  R --> P
  R --> V["Verification"]
  P --> M["Ledger / Active Memory"]
  G --> B["Boss Approval Records"]
  G --> L["License Approval Records"]
  G --> CD["Committee Decision Ledger"]
  V --> OUT["Per-engine JSON Outputs"]
```

## Contracts

`paideia_engines.contracts` defines shared objects:

- `EngineEvent`
- `ReviewLabel`
- `PromotionDecision`
- `QuarantineDecision`
- `default_local_policy()`

Contracts are intentionally small so every engine can stay independent.

## Engine Boundaries

| Engine | Owns | Does Not Own |
| --- | --- | --- |
| Data Acquisition | source decisions, license gates, acquisition manifests | curriculum design |
| Curriculum Mapping | learning units and standard coverage | scoring or promotion |
| Cultivation | blueprint, roadmaps, handoffs | scoring, promotion |
| Assessment | item bank, rubric result, transcript | memory promotion |
| Stress | scenario bank, resilience signal | promotion decision |
| Promotion | versioned ledger, quarantine, active memory route | task execution |
| Governance | policy evaluation, approval records, committee decisions | model output generation |
| Runtime | run trace, artifact manifest, replay evidence, checklist | learning update |
| Orchestration | config runner, CLI composition, output paths, verification summary | internal engine policy |

## Design Rule

No engine should silently perform another engine's decision. Stress can produce a promotion candidate signal, but only Promotion can create a promotion decision. Runtime can record evidence, but it cannot make memory active. Governance can block or allow a run, but it does not generate model output. The Config Runner composes engines, writes outputs, and emits a verification summary; it does not rewrite the meaning of any engine result.
