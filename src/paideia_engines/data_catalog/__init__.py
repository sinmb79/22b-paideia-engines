"""Data source catalog for Paideia engine training and evaluation assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class DatasetRecord:
    source_id: str
    title: str
    source_url: str
    provider: str
    license_tier: str
    acquisition_mode: str
    auto_download: bool
    school_levels: tuple[str, ...]
    subjects: tuple[str, ...]
    data_types: tuple[str, ...]
    engine_uses: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_seed_catalog() -> list[DatasetRecord]:
    """Return a conservative seed catalog of official or licensable sources.

    The catalog intentionally stores source metadata, not copyrighted contents.
    Restricted textbook content must be acquired manually under a valid license.
    """

    return [
        DatasetRecord(
            source_id="ncic_curriculum_originals",
            title="NCIC national curriculum originals and guides",
            source_url="https://ncic.re.kr/",
            provider="National Curriculum Information Center",
            license_tier="open_public",
            acquisition_mode="official_download_or_reference",
            auto_download=False,
            school_levels=("elementary", "middle", "high"),
            subjects=("all",),
            data_types=("curriculum_standard", "achievement_standard", "guide"),
            engine_uses=("cultivation", "assessment", "governance"),
            notes="Use as curriculum spine and achievement-standard mapping source.",
        ),
        DatasetRecord(
            source_id="data_go_kr_ncic_curriculum",
            title="MOE NCIC curriculum original and commentary file data",
            source_url="https://www.data.go.kr/data/15060742/fileData.do",
            provider="Ministry of Education / data.go.kr",
            license_tier="open_public",
            acquisition_mode="official_download_or_reference",
            auto_download=False,
            school_levels=("kindergarten", "elementary", "middle", "high", "special"),
            subjects=("all",),
            data_types=("curriculum_original", "commentary"),
            engine_uses=("cultivation", "assessment"),
            notes="Use to align grade, subject, domain, and achievement standards.",
        ),
        DatasetRecord(
            source_id="aihub_grade_subject_textbook_data",
            title="AI-Hub grade-level subject textbook data",
            source_url="https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71855",
            provider="AI-Hub",
            license_tier="login_or_agreement_required",
            acquisition_mode="account_download_after_terms_review",
            auto_download=False,
            school_levels=("elementary", "middle", "high"),
            subjects=("all",),
            data_types=("text", "image", "question_answer", "caption"),
            engine_uses=("cultivation", "assessment", "stress", "promotion"),
            notes="Licensed educational corpus built from textbook/reference materials; review AI-Hub terms before use.",
        ),
        DatasetRecord(
            source_id="aihub_math_problem_solving",
            title="AI-Hub math problem solving process data",
            source_url="https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71859",
            provider="AI-Hub",
            license_tier="login_or_agreement_required",
            acquisition_mode="account_download_after_terms_review",
            auto_download=False,
            school_levels=("elementary", "middle", "high"),
            subjects=("math",),
            data_types=("problem", "solution", "answer", "explanation", "image"),
            engine_uses=("assessment", "stress", "promotion"),
            notes="Useful for rubric scoring, solution-trace evaluation, and stress scenarios.",
        ),
        DatasetRecord(
            source_id="moe_csat_example_items",
            title="MOE CSAT example items and public guidance materials",
            source_url="https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=101085&lev=0&m=020402",
            provider="Ministry of Education",
            license_tier="open_public",
            acquisition_mode="official_download_or_reference",
            auto_download=False,
            school_levels=("high",),
            subjects=("integrated_social_studies", "integrated_science", "csat"),
            data_types=("example_item", "guidance", "policy_document"),
            engine_uses=("assessment", "stress", "governance"),
            notes="Public example items can seed assessment and stress-test patterns.",
        ),
        DatasetRecord(
            source_id="ebsi_national_exam_archives",
            title="EBSi national academic assessment archives",
            source_url="https://www.ebsi.co.kr/",
            provider="EBSi / metropolitan and provincial education offices",
            license_tier="public_reference_with_site_terms",
            acquisition_mode="manual_source_review_required",
            auto_download=False,
            school_levels=("high",),
            subjects=("korean", "math", "english", "korean_history", "social_studies", "science"),
            data_types=("exam", "answer_key", "explanation", "listening_audio"),
            engine_uses=("assessment", "stress", "promotion"),
            notes="Use only after checking official posting and site terms for each file.",
        ),
        DatasetRecord(
            source_id="digital_textbook_viewer_content",
            title="Digital textbook viewer content",
            source_url="https://dtbook.edunet.net/",
            provider="KERIS / publishers",
            license_tier="restricted_publisher_license",
            acquisition_mode="manual_license_required",
            auto_download=False,
            school_levels=("elementary", "middle", "high"),
            subjects=("all",),
            data_types=("textbook", "teacher_guide", "multimedia"),
            engine_uses=("cultivation", "assessment"),
            notes="Do not scrape or redistribute; use only through permitted viewer or explicit publisher license.",
        ),
        DatasetRecord(
            source_id="publisher_textbook_purchase_or_license",
            title="Publisher textbook and teacher-guide license packages",
            source_url="https://copyright.keris.or.kr/wft/fntLaw",
            provider="Textbook publishers / Education Copyright Support Center guidance",
            license_tier="restricted_publisher_license",
            acquisition_mode="manual_license_required",
            auto_download=False,
            school_levels=("elementary", "middle", "high"),
            subjects=("all",),
            data_types=("textbook", "teacher_guide", "workbook", "reference_book"),
            engine_uses=("cultivation", "assessment", "stress"),
            notes="Acquire by purchase, written permission, or valid compensation/licensing path before ingestion.",
        ),
    ]


def filter_by_engine(records: Iterable[DatasetRecord], engine_name: str) -> list[DatasetRecord]:
    engine = engine_name.strip().lower()
    return [record for record in records if engine in record.engine_uses]


def catalog_as_dicts(records: Iterable[DatasetRecord]) -> list[dict[str, object]]:
    return [record.to_dict() for record in records]


__all__ = ["DatasetRecord", "catalog_as_dicts", "default_seed_catalog", "filter_by_engine"]
