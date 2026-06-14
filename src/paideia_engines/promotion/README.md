# Promotion Engine

[한국어](README.ko.md)

The Promotion Engine decides whether reviewed experiences become active memory.

## Owns

- Versioned promotion ledger
- Quarantined experiences
- Quarantine reconsideration
- Promoted experience supersession
- Active memory routing

## Public API

- `PromotionEngine(owner, minimum_score=80)`
- `record_experience(...)`
- `reconsider_quarantined(...)`
- `supersede_promoted(...)`
- `route_active_memory(...)`

## Safety Boundary

This engine promotes only verified high-quality experiences and excludes quarantined or superseded entries from active memory.
