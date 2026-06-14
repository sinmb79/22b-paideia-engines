# 공개 자산 감사

[English](public_asset_audit.md)

이 문서는 공개 저장소에 포함해도 되는 것과 포함하면 안 되는 것을 정의합니다.

## 포함 가능

- `src/paideia_engines/` 아래 엔진 소스 코드
- `tests/` 아래 테스트
- `data/` 아래 공개 metadata catalog
- 샘플 교육과정 standards와 sample JSON config
- 문서와 릴리스 체크리스트

## 포함 금지

- 개인 음성 자산
- credential
- 제한 교과서 본문
- 개인 데이터
- 생성된 cache
- 개인 이미지
- 개인 폴더를 가리키는 로컬 절대경로
- 생성된 실행 산출물

## 현재 공개 데이터 경계

`data/catalog/seed_sources.json`와 `data/curriculum/sample_standards.json`는 metadata와 작은 synthetic/sample standards만 포함합니다. 제한 교과서 본문은 라이선스 또는 명시적 허가를 받은 뒤 저장소 밖에서 확보해야 합니다.

## 감사 명령

```powershell
rg -n "<release-sensitive-patterns>" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
```

릴리스 전에는 매칭이 없어야 합니다.
