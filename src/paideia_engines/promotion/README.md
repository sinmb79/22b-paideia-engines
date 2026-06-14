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
- `owner`, `minimum_score`, `ledger`, and `events` are read-only accessors.

`PromotionEngine(owner, minimum_score=80)` validates its trust config at initialization. `owner` must be a non-empty string without surrounding whitespace, and `minimum_score` must be an integer between 0 and 100.

Promotion gates are stricter than generic review helpers: only `review.status == "verified"` can promote memory or create a `PromotionDecision.from_review(...)` result. Generic `ReviewLabel.is_verified()` may accept `approved` or `passed`, but Promotion treats those statuses as insufficient for active memory.

`ledger`, `events`, returned promotion decisions, and active-memory routes are detached mutable snapshots. Mutating a returned snapshot is allowed by Python object semantics, but it never mutates engine internal state. Snapshot copying has a cost for large ledgers; high-volume use should prefer future persistence/replay backends instead of repeatedly materializing full in-memory ledgers.

## Safety Boundary

This engine promotes only verified high-quality experiences and excludes quarantined or superseded entries from active memory.
