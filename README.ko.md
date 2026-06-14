# 파이데이아 엔진

[English](README.md)

파이데이아 엔진은 AI 에이전트 성장 시스템을 만들기 위한 로컬 우선 Python 엔진 제품군입니다. 에이전트 자체도 중요한 결과물이지만, 그 안에 들어간 엔진들은 더 넓게 재사용할 수 있는 핵심 자산입니다.

이 저장소는 육성, 평가, 스트레스 리허설, 승급, 거버넌스, 런타임 추적, 오케스트레이션 엔진을 각각 독립적으로 사용할 수 있게 만들었습니다.

## 왜 필요한가

AI 에이전트의 훈련, 평가, 기억, 실행, 통제가 하나의 불투명한 루프에 섞이면 신뢰하기 어렵습니다. 파이데이아 엔진은 책임을 분리합니다.

- **육성 엔진**: 훈련 청사진과 커리큘럼 handoff를 만듭니다.
- **평가 엔진**: 결정론적 rubric과 transcript로 결과물을 평가합니다.
- **스트레스 엔진**: 어려운 상황을 리허설하되, 직접 기억을 승급하지 않습니다.
- **승급 엔진**: 검증된 고품질 경험만 승급하고 약한 경험은 격리합니다.
- **거버넌스 엔진**: 로컬 우선 정책, 보스 검토 게이트, 외부 업로드 제한을 다룹니다.
- **런타임 엔진**: trace와 acceptance checklist가 남는 실행 기록을 만듭니다.
- **오케스트레이션 엔진**: 여러 엔진을 하나의 성장 사이클로 조합합니다.

## 로컬 개발 설치

```powershell
git clone https://github.com/sinmb79/22b-paideia-engines.git
cd 22b-paideia-engines
python -m pip install -e .[dev]
python -m pytest tests -q
```

## 빠른 시작

```python
from paideia_engines.orchestration import PaideiaEngineSuite

suite = PaideiaEngineSuite()
cycle = suite.run_growth_cycle(
    learner_id="agent:analyst",
    role="research analyst",
    objectives=["evidence-first answers"],
    task="prepare evidence summary",
)

print(cycle["promotion_decision"]["status"])
```

예제 실행:

```powershell
python examples/basic_growth_cycle.py
```

## 엔진의 독립성

각 엔진은 class API와 결정론적 dictionary 출력을 갖습니다. 필요한 엔진만 골라 쓸 수 있습니다.

```python
from paideia_engines.promotion import PromotionEngine
from paideia_engines.contracts import ReviewLabel

engine = PromotionEngine(owner="agent:analyst")
decision = engine.record_experience(
    source="runtime",
    event={"summary": "Verified task result.", "skills": ["evidence_review"]},
    review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
)
```

## 문서

- [아키텍처](docs/architecture.ko.md)
- [Architecture in English](docs/architecture.md)

## 안전 기본값

- 로컬 우선 데이터 경계
- 외부 업로드 기본 차단
- 비공개 자산 접근 시 보스 검토 필요
- 런타임 결과는 기억 승급 전 검토 필요
- 격리된 경험은 활성 기억 라우팅에서 제외

## 라이선스

MIT
