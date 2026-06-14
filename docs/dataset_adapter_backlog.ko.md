# 데이터셋 어댑터 백로그

[English](dataset_adapter_backlog.md)

현재 저장소는 metadata와 예제를 포함하며, 전체 교과서나 시험지 데이터셋을 포함하지 않습니다. 데이터셋 어댑터는 합법적이고, manifest 기반이며, 로컬 우선이어야 합니다.

## Phase 7 구현

- `DataAcquisitionEngine.validate_acquired_sources(...)`
- `DataAcquisitionEngine.validate_manifest(...)`
- `CurriculumMappingEngine.load_standards_file(...)`
- `ItemBank.from_file(...)`
- 설정 기반 suite `acquisition_validation` 출력

구현된 어댑터는 이미 합법적으로 확보된 로컬 JSON 파일만 파싱합니다. 교과서를 다운로드하거나, 시험 아카이브를 scraping하거나, 제한 원본 파일을 저장소에 복사하지 않습니다.

## Phase 8 구현

- `parse_ncic_curriculum_csv(...)`
- `parse_assessment_items_csv(...)`
- `parse_aihub_math_items_json(...)`
- `build_public_exam_metadata_manifest(...)`
- Config runner parser 키: `ncic_csv`, `data_go_kr_csv`, `public_assessment_csv`, `aihub_json`, `aihub_csv`

Phase 8 parser는 로컬 CSV/JSON export만 읽습니다. HWP/PDF 교과서를 parsing하거나 시험 페이지를 crawling하지 않습니다.

## Phase 9 구현

- `diagnose_source_file(...)`
- `diagnose_source_fixture_pack(...)`
- CLI 명령: `diagnose-source`
- 공개 안전 fixture manifest: `examples/source_fixture_pack.json`

Phase 9 diagnostics layer는 parser pack을 release-ready로 보기 전에 fixture 파일 존재, hash, parser 지원 여부, 필수 header 또는 JSON field, parser 실행 완료, 최소 record 수를 검증합니다.

## Phase 10 구현

- `validate_configured_suite_outputs(...)`
- `validate_configured_suite_result(...)`
- CLI 명령: `validate-suite-output`
- 엔진별 output file, expected schema, 확보 자료 검증, 최종 verification, stress-to-promotion 경계, governance, runtime replayability에 대한 release-quality cross-check

Phase 10 validator는 이미 생성된 로컬 JSON output만 읽습니다. 엔진을 다시 실행하거나, source data를 다운로드하거나, promotion decision을 만들지 않습니다.

## 어댑터 우선순위

1. **공개 교육과정 standards importer**
   - 입력: 공식 공개 교육과정 파일 또는 수동 준비 JSON
   - 출력: `CurriculumStandard` mapping
   - 보호장치: provider attribution과 source URL 보존

2. **공개 평가 문항 importer**
   - 입력: 공개 예시 문항 또는 수동 라이선스 item bank
   - 출력: `AssessmentItem` record
   - 보호장치: 제한 페이지 scraping 금지

3. **확보 자료 manifest validator**
   - 입력: `acquired_sources.jsonl`
   - 출력: hash, license note, approver, missing field validation report
   - 보호장치: 제한 자료 승인 누락 시 fail closed

4. **공식 포맷별 parser 강화**
   - 입력: 유효한 manifest 아래 확보한 실제 공개 출처 CSV/JSON export
   - 출력: 정규화된 엔진 record와 parser diagnostics
   - 보호장치: 명시적 license evidence가 있기 전에는 HWP/PDF와 제한 원본 parsing을 공개 저장소 밖에 둠

## 보류

- 교과서 자동 다운로드
- 디지털 교과서 viewer content scraping
- 개인 training corpus의 외부 서비스 업로드
