"""Source-specific local parsers for public or licensed education files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from paideia_engines.assessment.item_bank import AssessmentItem, ItemBank
from paideia_engines.curriculum_mapping import CurriculumStandard
from paideia_engines.data_acquisition import DataAcquisitionEngine


NCIC_DEFAULTS = {
    "source_id": "ncic_curriculum_originals",
    "provider": "National Curriculum Information Center",
    "source_url": "https://ncic.re.kr/",
    "license_tier": "open_public",
}

PUBLIC_ASSESSMENT_DEFAULTS = {
    "source_id": "moe_csat_example_items",
    "provider": "Ministry of Education",
    "source_url": "https://www.moe.go.kr/",
    "license_tier": "open_public",
}

AIHUB_MATH_DEFAULTS = {
    "source_id": "aihub_math_problem_solving",
    "provider": "AI-Hub",
    "source_url": "https://www.aihub.or.kr/",
    "license_tier": "login_or_agreement_required",
}

EBSI_METADATA_DEFAULTS = {
    "source_id": "ebsi_national_exam_archives",
    "provider": "EBSi / metropolitan and provincial education offices",
    "source_url": "https://www.ebsi.co.kr/",
    "license_tier": "public_reference_with_site_terms",
}


def parse_ncic_curriculum_csv(
    path: str | Path,
    *,
    standard_version: str | None = None,
    source_id: str = NCIC_DEFAULTS["source_id"],
    provider: str = NCIC_DEFAULTS["provider"],
    source_url: str = NCIC_DEFAULTS["source_url"],
    license_tier: str = NCIC_DEFAULTS["license_tier"],
) -> list[CurriculumStandard]:
    """Parse an NCIC/data.go.kr-style curriculum CSV export.

    The parser accepts both English field names and common Korean headers used
    in manually exported education-standard spreadsheets.
    """

    source_path = Path(path)
    rows = _read_csv_dicts(source_path)
    standards: list[CurriculumStandard] = []
    for index, row in enumerate(rows, start=1):
        value = {
            "standard_id": _pick(row, "standard_id", "성취기준코드", "성취기준 ID", "성취기준ID", "코드"),
            "school_level": _pick(row, "school_level", "학교급", "학교급별", "학교급명"),
            "grade": _pick(row, "grade", "학년", "학년군", "대상학년"),
            "subject": _pick(row, "subject", "과목", "교과", "교과목"),
            "domain": _pick(row, "domain", "영역", "내용영역", "내용 영역"),
            "achievement": _pick(row, "achievement", "성취기준", "성취기준 해설", "기준"),
            "source_id": source_id,
            "provider": provider,
            "source_url": source_url,
            "license_tier": license_tier,
            "standard_version": standard_version,
            "imported_from": str(source_path.resolve()),
        }
        try:
            standards.append(CurriculumStandard.from_mapping(value))
        except ValueError as exc:
            raise ValueError(f"Invalid NCIC curriculum row {index}: {exc}") from exc
    return standards


def parse_assessment_items_csv(
    path: str | Path,
    *,
    source_id: str = PUBLIC_ASSESSMENT_DEFAULTS["source_id"],
    provider: str = PUBLIC_ASSESSMENT_DEFAULTS["provider"],
    source_url: str = PUBLIC_ASSESSMENT_DEFAULTS["source_url"],
    license_tier: str = PUBLIC_ASSESSMENT_DEFAULTS["license_tier"],
) -> ItemBank:
    """Parse a public or licensed assessment-item CSV export."""

    source_path = Path(path)
    rows = _read_csv_dicts(source_path)
    items = [
        _assessment_item_from_row(
            row,
            index=index,
            source_path=source_path,
            source_id=source_id,
            provider=provider,
            source_url=source_url,
            license_tier=license_tier,
        )
        for index, row in enumerate(rows, start=1)
    ]
    return ItemBank(items)


def parse_aihub_math_items_json(
    path: str | Path,
    *,
    source_id: str = AIHUB_MATH_DEFAULTS["source_id"],
    provider: str = AIHUB_MATH_DEFAULTS["provider"],
    source_url: str = AIHUB_MATH_DEFAULTS["source_url"],
    license_tier: str = AIHUB_MATH_DEFAULTS["license_tier"],
) -> ItemBank:
    """Parse a local AI-Hub-like math problem/solution JSON payload."""

    source_path = Path(path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        raw_items = payload.get("data", payload.get("items", []))
    elif isinstance(payload, list):
        raw_items = payload
    else:
        raise TypeError("AI-Hub math payload must be a mapping or list.")
    if not isinstance(raw_items, list):
        raise ValueError("AI-Hub math payload requires a data or items list.")

    items: list[AssessmentItem] = []
    for index, row in enumerate(raw_items, start=1):
        if not isinstance(row, dict):
            raise TypeError(f"data[{index}] must be a mapping.")
        item = AssessmentItem(
            item_id=str(_pick(row, "item_id", "id", "문항ID", default=f"aihub-math-{index:04d}")),
            standard_id=str(_pick(row, "standard_id", "curriculum_code", "성취기준코드")),
            gate_id=str(_pick(row, "gate_id", default="aihub_math_solution")),
            item_type=str(_pick(row, "item_type", default="solution_process")),
            prompt=str(_pick(row, "prompt", "question", "문제", "문항")),
            answer=str(_pick(row, "answer", "정답")),
            distractors=_as_list(_pick(row, "distractors", "wrong_answers", "오답", default=[])),
            explanation=str(_pick(row, "explanation", "solution", "풀이", "해설", default="")),
            rubric=_coerce_rubric(_pick(row, "rubric", default={"accuracy": 50, "process": 40, "clarity": 10})),
            source_id=source_id,
            provider=provider,
            source_url=source_url,
            imported_from=str(source_path.resolve()),
            license_tier=license_tier,
        )
        items.append(item)
    return ItemBank(items)


def build_public_exam_metadata_manifest(
    path: str | Path,
    *,
    approved_by: str,
    source_id: str = EBSI_METADATA_DEFAULTS["source_id"],
    provider: str = EBSI_METADATA_DEFAULTS["provider"],
    source_url: str = EBSI_METADATA_DEFAULTS["source_url"],
) -> list[dict[str, Any]]:
    """Build metadata-only acquired-source records for public exam indexes."""

    source_path = Path(path)
    rows = _read_csv_dicts(source_path)
    if not rows:
        raise ValueError("public exam metadata CSV must contain at least one row.")
    file_hash = DataAcquisitionEngine.hash_path(source_path)
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        records.append(
            {
                "schema": DataAcquisitionEngine.acquired_schema,
                "source_id": source_id,
                "title": _pick(row, "title", "제목", default=f"public exam metadata row {index}"),
                "provider": provider,
                "source_url": _pick(row, "source_url", "url", "URL", default=source_url),
                "license_tier": EBSI_METADATA_DEFAULTS["license_tier"],
                "acquisition_mode": "manual_source_review_required",
                "status": "acquired",
                "local_path": str(source_path.resolve()),
                "hash": file_hash,
                "license_note_path": None,
                "approved_by": approved_by,
                "content_scope": "metadata_only",
                "metadata": {
                    key: value
                    for key, value in row.items()
                    if value not in (None, "")
                },
                "engine_uses": ["assessment", "stress", "promotion"],
            }
        )
    return records


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            {str(key).strip(): (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def _pick(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def _assessment_item_from_row(
    row: dict[str, Any],
    *,
    index: int,
    source_path: Path,
    source_id: str,
    provider: str,
    source_url: str,
    license_tier: str,
) -> AssessmentItem:
    try:
        return AssessmentItem(
            item_id=str(_pick(row, "item_id", "문항ID", "id")),
            standard_id=str(_pick(row, "standard_id", "성취기준코드", "curriculum_code")),
            gate_id=str(_pick(row, "gate_id", "평가관문", default="unit_check")),
            item_type=str(_pick(row, "item_type", "문항유형", default="short_answer")),
            prompt=str(_pick(row, "prompt", "문항", "문제", "question")),
            answer=str(_pick(row, "answer", "정답")),
            distractors=_as_list(_pick(row, "distractors", "오답", "wrong_answers", default=[])),
            explanation=str(_pick(row, "explanation", "해설", "풀이", default="")),
            rubric=_coerce_rubric(_pick(row, "rubric", "채점기준", default={"accuracy": 100})),
            source_id=source_id,
            provider=provider,
            source_url=source_url,
            imported_from=str(source_path.resolve()),
            license_tier=license_tier,
        )
    except ValueError as exc:
        raise ValueError(f"Invalid assessment CSV row {index}: {exc}") from exc


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.replace(";", "|").split("|") if part.strip()]


def _coerce_rubric(value: Any) -> dict[str, int]:
    if isinstance(value, dict):
        return {str(key): int(score) for key, score in value.items()}
    text = str(value).strip()
    if not text:
        return {"accuracy": 100}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise TypeError("rubric must be a JSON object.")
    return {str(key): int(score) for key, score in parsed.items()}


__all__ = [
    "build_public_exam_metadata_manifest",
    "parse_aihub_math_items_json",
    "parse_assessment_items_csv",
    "parse_ncic_curriculum_csv",
]
