"""Assessment item bank models and deterministic gate construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AssessmentItem:
    item_id: str
    standard_id: str
    gate_id: str
    item_type: str
    prompt: str
    answer: str
    distractors: list[str]
    explanation: str
    rubric: dict[str, int]

    def __post_init__(self) -> None:
        required = {
            "item_id": self.item_id,
            "standard_id": self.standard_id,
            "gate_id": self.gate_id,
            "item_type": self.item_type,
            "prompt": self.prompt,
            "answer": self.answer,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"Missing assessment item fields: {', '.join(missing)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ItemBank:
    """Small deterministic item bank for local assessment workflows."""

    gate_schema = "paideia-assessment-gate/v1"

    def __init__(self, items: list[AssessmentItem] | None = None) -> None:
        self.items = list(items or [])
        self._by_id = {item.item_id: item for item in self.items}
        if len(self._by_id) != len(self.items):
            raise ValueError("Assessment item ids must be unique.")

    def get(self, item_id: str) -> AssessmentItem:
        try:
            return self._by_id[item_id]
        except KeyError as exc:
            raise KeyError(f"Unknown assessment item: {item_id}") from exc

    def select(
        self,
        *,
        gate_id: str | None = None,
        standard_ids: list[str] | None = None,
        item_types: list[str] | None = None,
    ) -> list[AssessmentItem]:
        standards = set(standard_ids or [])
        types = set(item_types or [])
        selected = []
        for item in self.items:
            if gate_id is not None and item.gate_id != gate_id:
                continue
            if standards and item.standard_id not in standards:
                continue
            if types and item.item_type not in types:
                continue
            selected.append(item)
        return selected

    def build_gate(self, gate_id: str, *, standard_ids: list[str] | None = None) -> dict[str, Any]:
        selected = self.select(gate_id=gate_id, standard_ids=standard_ids)
        return {
            "schema": self.gate_schema,
            "gate_id": gate_id,
            "standard_ids": list(standard_ids or sorted({item.standard_id for item in selected})),
            "item_count": len(selected),
            "items": [item.to_dict() for item in selected],
        }


__all__ = ["AssessmentItem", "ItemBank"]
