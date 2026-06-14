# 파이데이아 엔진 데이터 확보 계획

[English](data_acquisition.md)

## 원칙

파이데이아 엔진에 들어갈 데이터는 먼저 합법성과 추적성을 확보해야 합니다. 특히 교과서, 참고서, 교사용 지도서, 시험지, 해설지는 학습 가치가 높지만 저작권과 이용 조건이 다릅니다.

따라서 데이터는 다음 네 단계로 나눕니다.

| 단계 | 데이터 | 상태 | 처리 |
| --- | --- | --- | --- |
| 0 | 국가 교육과정, 성취기준, 공개 정책 문서 | 공개 자료 | curriculum spine으로 우선 확보 |
| 1 | AI-Hub 교육 데이터 | 로그인/이용약관 필요 | 약관 확인 후 수동 다운로드 |
| 2 | 수능/모의평가/전국연합 등 공개 시험 자료 | 공개 게시 범위 확인 필요 | 출처/연도/과목별 매니페스트화 |
| 3 | 출판사 교과서, 디지털교과서, 교사용 지도서 | 제한 자료 | 구매/허락/계약 없이는 수집 금지 |

## 우선 확보 출처

1. **NCIC 국가교육과정정보센터**
   - URL: https://ncic.re.kr/
   - 용도: 학년, 과목, 성취기준, 교육과정 구조
   - 연결 엔진: `cultivation`, `assessment`, `governance`

2. **data.go.kr 교육부 NCIC 교육과정 원문 및 해설서**
   - URL: https://www.data.go.kr/data/15060742/fileData.do
   - 용도: 교육과정 원문/해설서 기반 구조화
   - 연결 엔진: `cultivation`, `assessment`

3. **AI-Hub 교과 단계별 교과 데이터**
   - URL: https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71855
   - 용도: 교과서/참고서 기반 텍스트, 이미지, 질의응답, 캡션
   - 연결 엔진: `cultivation`, `assessment`, `stress`, `promotion`
   - 주의: AI-Hub 계정과 이용약관 확인 후 다운로드

4. **AI-Hub 수학 교과 문제 풀이과정 데이터**
   - URL: https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71859
   - 용도: 문제, 정답, 오답, 풀이과정, 해설
   - 연결 엔진: `assessment`, `stress`, `promotion`
   - 주의: AI-Hub 계정과 이용약관 확인 후 다운로드

5. **교육부 수능 예시문항/안내자료**
   - URL: https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=101085&lev=0&m=020402
   - 용도: 평가 문항 패턴, 시험 안내, 공공누리 조건 자료
   - 연결 엔진: `assessment`, `stress`, `governance`

6. **EBSi 및 시도교육청 공개 학력평가 자료**
   - URL: https://www.ebsi.co.kr/
   - 용도: 문제지, 정답, 해설, 듣기 파일
   - 연결 엔진: `assessment`, `stress`, `promotion`
   - 주의: 각 파일의 공식 게시 여부와 이용 조건을 확인해야 합니다.

7. **디지털교과서/출판사 교과서**
   - URL: https://dtbook.edunet.net/
   - 용도: 실제 교과서 본문과 멀티미디어
   - 연결 엔진: `cultivation`, `assessment`
   - 주의: 디지털교과서와 출판사 교과서는 무단 스크래핑/재배포/2차 저작물 활용 금지 영역입니다. 명시적 허락 또는 구매/계약이 필요합니다.

## 저장 구조 제안

실제 대용량 데이터는 GitHub에 넣지 않습니다. 로컬 또는 별도 스토리지에 두고, 레포에는 매니페스트만 둡니다.

```text
data/
  catalog/
    seed_sources.json
    acquired_sources.jsonl
  raw/
    <source_id>/
  processed/
    cultivation/
    assessment/
    stress/
    promotion/
  licenses/
    <source_id>.md
```

## 매니페스트 필드

```json
{
  "source_id": "aihub_math_problem_solving",
  "title": "AI-Hub math problem solving process data",
  "provider": "AI-Hub",
  "source_url": "https://...",
  "license_tier": "login_or_agreement_required",
  "acquisition_mode": "account_download_after_terms_review",
  "school_levels": ["elementary", "middle", "high"],
  "subjects": ["math"],
  "engine_uses": ["assessment", "stress", "promotion"],
  "local_path": "data/raw/aihub_math_problem_solving",
  "hash": "sha256:...",
  "status": "planned"
}
```

## Phase 7 어댑터 계약

구현된 경로는 다음 순서를 따릅니다.

```text
합법적으로 확보한 로컬 파일 -> 확보 자료 manifest -> 검증 리포트 -> 엔진 어댑터
```

- `validate_manifest(...)`와 `validate_acquired_sources(...)`는 source id, 로컬 경로, hash, 승인자, content scope, license note 필요 여부를 검증합니다.
- `CurriculumMappingEngine.load_standards_file(...)`은 이미 확보한 공개 교육과정 JSON을 `CurriculumStandard`로 변환합니다.
- `ItemBank.from_file(...)`은 이미 확보한 공개 또는 라이선스 문항 JSON을 `AssessmentItem`으로 변환합니다.
- 설정 기반 suite는 교육과정 매핑 전에 `02_acquisition_validation.json`, 마지막에 `10_verification.json`을 남깁니다.

제한 교과서나 디지털교과서 자료는 `metadata_only` 범위일 때만 license note 없이 통과할 수 있습니다. 본문 전체를 다루려면 유효한 license 또는 terms-review note가 필요하며, 없으면 차단됩니다.

## Phase 8 출처별 파서

현재 source-specific parser 계층은 로컬 CSV/JSON export를 지원합니다.

- NCIC/data.go.kr 형식 교육과정 CSV를 `CurriculumStandard`로 변환
- 공개 평가 문항 CSV를 `ItemBank`로 변환
- AI-Hub식 수학 문제 JSON label을 `ItemBank`로 변환
- 공개 시험 metadata CSV를 metadata-only 확보 자료 record로 변환

parser 계층은 확보 자료 검증 이후에만 실행됩니다. Parser 파일은 `data.acquired_sources` 또는 `data.manifest_path`에 포함되어 hash 검증을 통과해야 하며, 설정한 parser/source 조합이 맞아야 사용할 수 있습니다.

## Phase 9 출처 진단

출처 진단은 릴리스 전에 공개 가능한 fixture pack을 검증합니다. 새 데이터를 확보하지 않고, 로컬 sample 파일을 검사하고, hash를 계산하고, 필수 field를 확인하고, 선택한 parser를 실행한 뒤 record 수를 보고합니다.

```powershell
python -m paideia_engines.cli diagnose-source --manifest examples/source_fixture_pack.json --output .paideia-runs/source-diagnostics.json
```

## Phase 11 Manifest diagnostics

확보 자료 manifest diagnostics는 릴리스 전이나 더 큰 로컬 corpus를 엔진에 연결하기 전에 JSONL manifest 자체를 검증합니다. 리포트는 JSONL parsing, acquired-source schema, 중복 source/path record, 지원 content scope, hash와 license note 검증, auto-download 요청, 공개 릴리스에 부적합한 non-open full-content record를 확인합니다.

```powershell
python -m paideia_engines.cli diagnose-manifest --manifest examples/acquired_sources_manifest.jsonl --output .paideia-runs/manifest-diagnostics.json
```

`--allow-local-only-full-content`는 보스가 로컬 저장과 license evidence를 승인한 private local run에서만 사용합니다. 공개 GitHub release에는 이 옵션을 사용하지 않습니다.

## 금지 사항

- 디지털교과서 뷰어에서 콘텐츠를 자동 추출하지 않습니다.
- 출판사 교과서 PDF/이미지를 무단 수집하지 않습니다.
- 구매한 개인 자료를 공개 GitHub에 올리지 않습니다.
- 라이선스가 불명확한 블로그/카페/사설 사이트 자료를 학습 원천으로 삼지 않습니다.
- 시험 시행 전 자료나 유출 의혹 자료는 절대 사용하지 않습니다.

## 다음 작업

1. `data/catalog/seed_sources.json` 생성
2. AI-Hub 계정으로 교육 데이터 이용약관 확인
3. NCIC 교육과정 문서를 학년/과목/성취기준 단위로 구조화
4. 공개 시험 자료는 연도, 학년, 과목, 출처 URL, 이용조건을 먼저 매니페스트화
5. 출판사 교과서는 별도 라이선스 확보 후 로컬 비공개 저장소로만 연결
