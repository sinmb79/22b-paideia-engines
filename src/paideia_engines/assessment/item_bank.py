"""Assessment item bank models and deterministic gate construction."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
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
    source_id: str | None = None
    provider: str | None = None
    source_url: str | None = None
    imported_from: str | None = None
    license_tier: str | None = None

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
        return {key: value for key, value in asdict(self).items() if value is not None}


class ItemBank:
    """Small deterministic item bank for local assessment workflows."""

    gate_schema = "paideia-assessment-gate/v1"

    def __init__(self, items: list[AssessmentItem] | None = None) -> None:
        self.items = list(items or [])
        self._by_id = {item.item_id: item for item in self.items}
        if len(self._by_id) != len(self.items):
            raise ValueError("Assessment item ids must be unique.")

    @classmethod
    def from_file(cls, path: str | Path) -> "ItemBank":
        """Build an item bank from an already-acquired local JSON file."""

        source_path = Path(path)
        with source_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, list):
            raw_items = payload
            metadata: dict[str, Any] = {}
        elif isinstance(payload, dict):
            raw_items = payload.get("items")
            metadata = {
                key: payload.get(key)
                for key in ("source_id", "provider", "source_url", "license_tier")
                if payload.get(key) is not None
            }
        else:
            raise TypeError("Assessment items payload must be a mapping or list.")

        if not isinstance(raw_items, list):
            raise ValueError("Assessment items payload requires an items list.")

        items: list[AssessmentItem] = []
        for index, item in enumerate(raw_items, start=1):
            if not isinstance(item, dict):
                raise TypeError(f"items[{index}] must be a mapping.")
            merged = {
                **metadata,
                **item,
                "imported_from": item.get("imported_from", str(source_path.resolve())),
            }
            try:
                items.append(cls._item_from_mapping(merged))
            except ValueError as exc:
                raise ValueError(f"Invalid assessment item at items[{index}]: {exc}") from exc
        return cls(items)

    @staticmethod
    def _item_from_mapping(value: dict[str, Any]) -> AssessmentItem:
        required = ["item_id", "standard_id", "gate_id", "item_type", "prompt", "answer"]
        missing = [key for key in required if not str(value.get(key, "")).strip()]
        if missing:
            raise ValueError(f"Missing assessment item fields: {', '.join(missing)}")
        distractors = value.get("distractors", [])
        if not isinstance(distractors, list):
            raise TypeError("distractors must be a list.")
        rubric = value.get("rubric", {"accuracy": 100})
        if not isinstance(rubric, dict):
            raise TypeError("rubric must be a mapping.")
        return AssessmentItem(
            item_id=str(value["item_id"]),
            standard_id=str(value["standard_id"]),
            gate_id=str(value["gate_id"]),
            item_type=str(value["item_type"]),
            prompt=str(value["prompt"]),
            answer=str(value["answer"]),
            distractors=[str(item) for item in distractors],
            explanation=str(value.get("explanation", "")),
            rubric={str(key): int(weight) for key, weight in rubric.items()},
            source_id=_optional_str(value.get("source_id")),
            provider=_optional_str(value.get("provider")),
            source_url=_optional_str(value.get("source_url")),
            imported_from=_optional_str(value.get("imported_from")),
            license_tier=_optional_str(value.get("license_tier")),
        )

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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["AssessmentItem", "ItemBank"]
