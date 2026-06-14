# Governance Engine

[한국어](README.ko.md)

The Governance Engine evaluates local-first policy and records approvals.

## Owns

- Policy rule evaluation
- Boss approval records
- License approval records
- Committee decision trails
- External upload blocking

## Public API

- `GovernanceEngine(policy=None)`
- `create_board(program_id)`
- `evaluate_policy(action, context=None)`
- `record_approval(...)`
- `record_committee_decision(...)`
- `review_action(action, context=None)`

## Safety Boundary

External uploads remain blocked by default. Approval records do not override hard upload bans.
