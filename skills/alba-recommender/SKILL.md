---
name: alba-recommender
description: 전남대 클린알바맵 기반 맞춤형 알바 추천 스킬. 사용자가 알바를 찾거나, 일자리를 추천받고 싶거나, 전남대 근처 알바를 검색하거나, 특정 상권/업종/조건에 맞는 아르바이트를 원할 때 반드시 이 스킬을 사용한다. "알바 추천해줘", "어디 알바 있어", "클린지수 높은 곳", "예대 근처 알바" 같은 표현이 나오면 즉시 실행한다.
---

# 알바 맞춤 추천 스킬 (alba-recommender)

전남대 인근 5개 상권 업체의 **누적 유저 리뷰**를 8개 객관 기준으로 분석하여 클린지수를 동적 산출하고, 조건에 맞는 알바를 추천한다.

## 아키텍처

```
add_review.py  ─→  data/{업체id}.json  ─→  recommend.py
   리뷰 추가              누적 저장         ┌─ 의도 분류 (LLM)
   LLM 분석              클린지수 갱신      │
                                          ├─ SEARCH  → 업체명/상권/업종 매칭
                                          └─ RECOMMEND → 조건 파싱 → 필터링 → LLM 추천
```

- 리뷰가 추가될 때마다 클린지수가 자동으로 재산출된다
- 단일 리뷰가 아닌 **전체 누적 리뷰의 위반율 평균**으로 점수를 결정한다
- 모든 검색/추천 요청은 먼저 의도 분류를 거쳐 알맞은 경로로 처리된다

## 스크립트

### 리뷰 추가 (add_review.py)

```bash
# 기존 사업장에 리뷰 추가
python ./scripts/add_review.py 스타벅스_상대점 "월급은 제때 나왔지만 쉬는 시간이 부족했어요."

# 신규 사업장 등록 + 리뷰
python ./scripts/add_review.py --name "카페 온도" --area 후문 --industry 카페 "계약서 작성하고 주휴수당도 받았어요."

# stdin JSON
echo '{"name": "투썸 정문점", "area": "정문", "industry": "카페", "review": "급여 제때 나왔습니다."}' | python ./scripts/add_review.py
```

### 검색 및 추천 (recommend.py)

입력을 자동으로 분류하여 SEARCH 또는 RECOMMEND 경로로 처리한다.

```bash
# SEARCH — 업체명·상권·업종 단순 검색
python ./scripts/recommend.py "스타벅스"
python ./scripts/recommend.py "상대 카페"

# RECOMMEND — 조건 기반 맞춤 추천 (누적 리뷰 종합)
python ./scripts/recommend.py "주휴수당 챙겨주는 예대 카페"
python ./scripts/recommend.py "클린지수 80 이상 급여 지연 없는 알바 추천해줘"
```

## 클린지수 산출 공식

$$\text{클린지수} = 100 - \sum_{i=1}^{8} \left(\frac{\text{위반 언급 수}_i}{\text{전체 리뷰 수}} \times \frac{100}{8}\right)$$

- 항목당 최대 배점: **12.5점** (100 ÷ 8)
- 리뷰가 누적될수록 위반율이 안정화되어 신뢰도가 높아진다

## 클린지수 산출 기준 (8개 객관 항목)

| # | 위반 항목 (cautions) | 준수 항목 (highlights) |
|---|---|---|
| 1 | 근로계약서 미작성 | 근로계약서 작성 |
| 2 | 최저시급 미준수 | 최저시급 준수 |
| 3 | 주휴수당 미지급 | 주휴수당 지급 |
| 4 | 휴게시간 부족 | 충분한 휴게시간 보장 |
| 5 | 급여지급 지연 | 정시 급여지급 |
| 6 | 사전 협의 없는 스케줄 변경 | 사전 협의된 스케줄 관리 |
| 7 | 반복적이고 지속적인 대타요구 및 강요 | 합리적인 대타 요청 |
| 8 | 초과근무 급여 미지급 | 초과근무 급여 지급 |

> **참고**: 동시간대 업무자 수는 점수 배점에서 제외되며, 사업장 요약 정보에 부가적인 태그(additional_info) 형태로만 제공됩니다.

- **cautions**: 위반율 ≥ 30% (리뷰 2건 이상 기준)
- **highlights**: 위반 언급 0건

## 의도 분류 기준

| 의도 | 조건 | 예시 |
|---|---|---|
| **SEARCH** | 업체명·상권명·업종명 등 명사형 단순 입력 | "스타벅스", "상대 카페", "GS25" |
| **RECOMMEND** | 근무조건·복지·환경을 포함하는 문장형 또는 복합 키워드 | "주휴수당 챙겨주는 카페", "휴게시간 넉넉한 곳" |

## 출력 형식

### add_review.py
```json
{
  "business_id": "스타벅스_상대점",
  "name": "스타벅스 상대점",
  "clean_score": 96,
  "review_count": 6,
  "violation_summary": {"휴게시간 부족": 1},
  "last_updated": "2026-05-13"
}
```

### recommend.py — SEARCH
```json
{
  "intent": "SEARCH",
  "search_term": "스타벅스",
  "count": 1,
  "results": [
    {
      "name": "스타벅스 상대점",
      "area": "상대",
      "industry": "카페",
      "clean_score": 94,
      "review_count": 6,
      "highlights": ["근로계약서 작성", "최저시급 준수", "주휴수당 지급", "정시 급여지급"],
      "cautions": []
    }
  ]
}
```

### recommend.py — RECOMMEND
```json
{
  "intent": "RECOMMEND",
  "recommendations": [
    {
      "rank": 1,
      "name": "스타벅스 상대점",
      "area": "상대",
      "industry": "카페",
      "clean_score": 94,
      "review_count": 6,
      "highlights": ["주휴수당 지급", "정시 급여지급"],
      "cautions": [],
      "reason": "6건의 누적 리뷰에서 급여 관련 위반이 없고 클린지수가 높습니다."
    }
  ],
  "summary": "추천 결과 요약",
  "parsed_preferences": {"area": "상대", "industry": "카페", "min_clean_score": null, "avoid_list": []}
}
```

## 대상 상권

| 상권 | 별칭 |
|---|---|
| 상대 | 상대, 상과대 |
| 예대 | 예대, 예술대 |
| 정문 | 정문, 전남대 정문 |
| 후문 | 후문, 전남대 후문 |
| 전철우 | 전철우, 전철우 사거리 |

## 데이터 저장 구조

`data/{business_id}.json` 파일에 업체별로 누적 저장된다.

```json
{
  "business_id": "카페_봄봄",
  "name": "카페 봄봄",
  "area": "예대",
  "industry": "카페",
  "reviews": [
    {
      "id": "r0001",
      "text": "원본 리뷰 텍스트",
      "criteria_flags": {"근로계약서 미작성": false, "휴게시간 부족": true, ...},
      "date": "2026-05-13"
    }
  ],
  "aggregate": {
    "review_count": 5,
    "criteria_violation_counts": {"휴게시간 부족": 2, ...},
    "clean_score": 91,
    "last_updated": "2026-05-13"
  }
}
```

## 환경 설정

`UPSTAGE_API_KEY` 환경변수가 필요하다. `.env.example` 참고: `./assets/.env.example`
