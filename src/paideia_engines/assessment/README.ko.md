# 평가 엔진

[English](README.md)

평가 엔진은 결정적 rubric과 문항 bank로 결과물을 평가합니다.

## 책임

- Rubric 평가
- Assessment transcript
- 문항 bank scoring
- Review label 후보 출력

## 공개 API

- `AssessmentEngine(item_bank=None)`
- `evaluate(gate_id, submission)`
- `build_transcript(learner_id, results)`
- `evaluate_item_response(item_id, response)`
- `AssessmentItem`
- `ItemBank`

## 안전 경계

이 엔진은 review label 후보를 만들 수 있습니다. 기억을 직접 승급하지 않습니다.
