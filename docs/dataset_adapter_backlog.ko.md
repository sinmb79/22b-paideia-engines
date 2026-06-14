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

4. **설정 기반 suite output validator**
   - 입력: 엔진별 JSON output
   - 출력: release-quality validation report
   - 보호장치: `02_acquisition_validation.json`, `10_verification.json`, stress-to-promotion 직접 결정 없음 확인

## 보류

- 교과서 자동 다운로드
- 디지털 교과서 viewer content scraping
- 개인 training corpus의 외부 서비스 업로드
