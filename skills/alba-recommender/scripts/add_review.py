#!/usr/bin/env python3
"""
add_review.py — 사업장 리뷰 추가 및 클린지수 동적 갱신

사용법:
    # 기존 사업장에 리뷰 추가
    python add_review.py 스타벅스_상대점 "월급은 정시에 나왔지만 쉬는 시간이 부족했어요."

    # 신규 사업장 등록 + 리뷰 추가
    python add_review.py --name "카페 봄봄" --area 예대 --industry 카페 "리뷰 텍스트"

    # stdin JSON 입력
    echo '{"name": "카페 봄봄", "area": "예대", "industry": "카페", "review": "..."}' | python add_review.py
"""

import os, sys, json, argparse, re
from datetime import date
from pathlib import Path
from openai import OpenAI

UPSTAGE_API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    print(json.dumps({"error": "UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다."}, ensure_ascii=False))
    sys.exit(1)

client = OpenAI(api_key=UPSTAGE_API_KEY, base_url="https://api.upstage.ai/v1")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CRITERIA_KEYS = [
    "근로계약서 미작성",
    "최저시급 미준수",
    "주휴수당 미지급",
    "휴게시간 부족",
    "급여지급 지연",
    "사전 협의 없는 스케줄 변경",
    "반복적이고 지속적인 대타요구 및 강요",
    "동시간대 업무자 부족",
    "초과근무 급여 미지급",
]

WEIGHT = 100 / len(CRITERIA_KEYS)  # 항목당 ≈ 11.11점

ANALYZE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "criteria_flags",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {k: {"type": "boolean"} for k in CRITERIA_KEYS},
            "required": CRITERIA_KEYS,
            "additionalProperties": False,
        },
    },
}

ANALYZE_SYSTEM = """당신은 알바 근무환경 분석 전문가입니다.
주어진 리뷰에서 아래 9개 클린지수 위반 항목이 언급되는지 판단하세요.
리뷰에서 해당 항목의 위반이 명확히 언급된 경우만 true, 그렇지 않으면 false로 표시하세요.

판단 기준:
1. 근로계약서 미작성 — 근로계약서를 작성하지 않았다고 언급된 경우
2. 최저시급 미준수 — 최저시급보다 적게 받았다고 언급된 경우
3. 주휴수당 미지급 — 주휴수당을 받지 못했다고 언급된 경우
4. 휴게시간 부족 — 법정 휴게시간이 보장되지 않았다고 언급된 경우
5. 급여지급 지연 — 급여가 늦게 지급되었다고 언급된 경우
6. 사전 협의 없는 스케줄 변경 — 공지 없이 갑자기 스케줄이 변경된 경우
7. 반복적이고 지속적인 대타요구 및 강요 — 대타를 강요당했다고 언급된 경우
8. 동시간대 업무자 부족 — 혼자 일하거나 인력이 부족하다고 언급된 경우
9. 초과근무 급여 미지급 — 초과근무 수당을 받지 못했다고 언급된 경우

항상 한국어로 응답하세요."""


def slugify(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip())


def load_business(business_id: str) -> dict | None:
    path = DATA_DIR / f"{business_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_business(data: dict) -> None:
    path = DATA_DIR / f"{data['business_id']}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def new_business(business_id: str, name: str, area: str, industry: str) -> dict:
    return {
        "business_id": business_id,
        "name": name,
        "area": area,
        "industry": industry,
        "reviews": [],
        "aggregate": {
            "review_count": 0,
            "criteria_violation_counts": {k: 0 for k in CRITERIA_KEYS},
            "clean_score": 100,
            "last_updated": str(date.today()),
        },
    }


def analyze_criteria(review_text: str) -> dict:
    resp = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": ANALYZE_SYSTEM},
            {"role": "user", "content": f"리뷰:\n{review_text}"},
        ],
        response_format=ANALYZE_SCHEMA,
        temperature=0.1,
        max_tokens=256,
    )
    return json.loads(resp.choices[0].message.content)


def recalculate_score(agg: dict) -> int:
    n = agg["review_count"]
    if n == 0:
        return 100
    deduction = sum(
        (agg["criteria_violation_counts"][k] / n) * WEIGHT
        for k in CRITERIA_KEYS
    )
    return max(0, round(100 - deduction))


def add_review(business: dict, review_text: str) -> dict:
    flags = analyze_criteria(review_text)

    review_id = f"r{len(business['reviews']) + 1:04d}"
    business["reviews"].append({
        "id": review_id,
        "text": review_text,
        "criteria_flags": flags,
        "date": str(date.today()),
    })

    agg = business["aggregate"]
    agg["review_count"] += 1
    for k in CRITERIA_KEYS:
        if flags[k]:
            agg["criteria_violation_counts"][k] += 1
    agg["clean_score"] = recalculate_score(agg)
    agg["last_updated"] = str(date.today())

    save_business(business)
    return business


def main():
    if not sys.stdin.isatty():
        data = json.loads(sys.stdin.read().strip())
        review_text = data.pop("review", "")
        business_id = data.get("business_id") or slugify(data.get("name", "unknown"))
        business = load_business(business_id) or new_business(
            business_id,
            data.get("name", business_id),
            data.get("area", "미지정"),
            data.get("industry", "기타"),
        )
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("positional", nargs="*")
        parser.add_argument("--name")
        parser.add_argument("--area")
        parser.add_argument("--industry")
        args = parser.parse_args()

        if args.name:
            business_id = slugify(args.name)
            business = load_business(business_id) or new_business(
                business_id, args.name,
                args.area or "미지정",
                args.industry or "기타",
            )
            review_text = " ".join(args.positional)
        elif len(args.positional) >= 2:
            business_id = args.positional[0]
            review_text = " ".join(args.positional[1:])
            business = load_business(business_id)
            if not business:
                print(json.dumps(
                    {"error": f"'{business_id}' 사업장 없음. --name --area --industry 옵션으로 신규 등록하세요."},
                    ensure_ascii=False,
                ))
                sys.exit(1)
        else:
            print(json.dumps(
                {"error": "사용법: add_review.py <business_id> '리뷰' 또는 --name '업체명' --area 지역 --industry 업종 '리뷰'"},
                ensure_ascii=False,
            ))
            sys.exit(1)

    if not review_text.strip():
        print(json.dumps({"error": "리뷰 텍스트를 입력해주세요."}, ensure_ascii=False))
        sys.exit(1)

    result = add_review(business, review_text)
    agg = result["aggregate"]

    print(json.dumps({
        "business_id": result["business_id"],
        "name": result["name"],
        "clean_score": agg["clean_score"],
        "review_count": agg["review_count"],
        "violation_summary": {
            k: v for k, v in agg["criteria_violation_counts"].items() if v > 0
        },
        "last_updated": agg["last_updated"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
