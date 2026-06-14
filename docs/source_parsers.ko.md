# 출처별 파서

[English](source_parsers.md)

Phase 8에서는 로컬 출처별 파서를 추가합니다. 이 파서들은 다운로드, 스크래핑, 보호 파일 우회를 하지 않습니다. 확보 자료 검증을 통과한 로컬 파일만 내부 표준 스키마로 정규화합니다.

## 지원 입력

| Parser | 입력 | 출력 | 경계 |
| --- | --- | --- | --- |
| `ncic_csv` | NCIC/data.go.kr 형식 교육과정 CSV export | `CurriculumStandard` record | 공개 교육과정 metadata와 성취기준만 |
| `public_assessment_csv` | 공개 또는 라이선스 평가 문항 CSV | `ItemBank` | 제한 페이지 스크래핑 금지 |
| `aihub_json` | AI-Hub식 수학 문제 JSON label | `ItemBank` | 확보 자료 검증에서 terms/license note 필요 |
| `aihub_csv` | AI-Hub식 수학 문제 CSV label | `ItemBank` | 확보 자료 검증에서 terms/license note 필요 |
| `ebsi_metadata_csv` | 공개 시험 metadata CSV | metadata-only 확보 자료 record | PDF/HWP에서 문항을 생성하지 않음 |

## Config Runner 키

```json
{
  "curriculum": {
    "standards_path": "source_samples/ncic_curriculum_sample.csv",
    "parser": "ncic_csv"
  },
  "assessment": {
    "items_path": "source_samples/aihub_math_sample.json",
    "parser": "aihub_json"
  }
}
```

해당 파일 경로는 `data.acquired_sources` 또는 `data.manifest_path`에도 포함되어야 하며, hash/license 검증을 통과해야 parser가 실행됩니다.
Config Runner가 parser를 호출할 때는 검증된 `source_id`, `provider`, `source_url`, `license_tier`를 정규화 결과에 그대로 전달해서 후속 엔진이 출처 표시를 유지할 수 있게 합니다.

## 예제

```powershell
python examples/source_specific_parsers.py
python -m paideia_engines.cli diagnose-source --manifest examples/source_fixture_pack.json --output .paideia-runs/source-diagnostics.json
```

## 진단 리포트

Phase 9에서는 공개 가능한 fixture pack용 parser diagnostics를 추가합니다. 진단 리포트는 파일 존재, SHA-256 hash, 지원 parser, 확장자, 필수 header 또는 JSON field, parser 실행 완료, 최소 record 수를 확인합니다. fixture pack은 metadata/sample 전용이며 제한 교과서나 시험 본문을 포함하지 않습니다.

## 비목표

- HWP/PDF 교과서 parsing
- 디지털교과서 viewer scraping
- EBSi 시험 페이지 crawling
- AI-Hub 다운로드 자동화
- 학습 corpus 외부 업로드
