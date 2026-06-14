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
- AI-Hub downloaded corpus
- 시험지 PDF, HWP/HWPX, archive, audio, video 원본
- 개인 데이터
- 생성된 cache
- 개인 이미지
- 개인 폴더를 가리키는 로컬 절대경로
- private absolute path가 포함된 acquired-source manifest
- 생성된 실행 산출물

## 현재 공개 데이터 경계

`data/catalog/seed_sources.json`와 `data/curriculum/sample_standards.json`는 metadata와 작은 synthetic/sample standards만 포함합니다. 제한 교과서 본문은 라이선스 또는 명시적 허가를 받은 뒤 저장소 밖에서 확보해야 합니다.

`examples/acquired_sources_manifest.jsonl`은 작은 sample JSONL만 가리키는 공개 안전 manifest 예제입니다. 교과서, 시험 archive, AI-Hub download, licensed corpus용 실제 acquired-source manifest는 metadata-only이고 private absolute path가 없는 경우가 아니라면 공개 저장소 밖에 두어야 합니다.

## 감사 명령

```powershell
rg -n "([O]PENAI_API_KEY|[A]NTHROPIC_API_KEY|[G]ITHUB_TOKEN|github[_]pat_|gh[p]_|\bsk-[A-Za-z0-9]{16,}|[B]EGIN (RSA|OPENSSH|PRIVATE) KEY|passw[o]rd\s*=|secr[e]t\s*=)" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
```

릴리스 전에는 매칭이 없어야 합니다.
