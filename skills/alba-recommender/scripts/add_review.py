#!/usr/bin/env python3
"""
add_review.py — 사업장 리뷰 추가 및 클린지수 동적 갱신

프론트엔드에서 사용자가 직접 체크한 O/X 결과를 받아 클린지수를 산출한다.
LLM 분석 없이 체크리스트 데이터만으로 단순 산수(100 - 위반항목수 × 12.5)로 계산한다.
주관식 텍스트는 점수에 관여하지 않고 저장만 된다.

사용법:
    # stdin JSON 입력 (프론트엔드 연동 주요 방식)
    echo '{
      "name": "카페 봄봄", "area": "예대", "industry": "카페",
      "criteria_flags": {
        "근로계약서 미작성": false,
        "최저시급 미준수": false,
        "주휴수당 미지급": false,
        "휴게시간 부족": true,
        "급여지급 지연": false,
        "사전 협의 없는 스케줄 변경": false,
        "반복적이고 지속적인 대타요구 및 강요": false,
        "초과근무 급여 미지급": false
      },
      "review_text": "쉬는 시간이 부족했어요."
    }' | python add_review.py

    # CLI — 기존 사업장에 위반 항목 지정
    python add_review.py 스타벅스_상대점 --violations "휴게시간 부족" --review "쉬는 시간이 없었어요."

    # 신규 사업장 등록
    python add_review.py --name "카페 온도" --area 후문 --industry 카페 --violations "급여지급 지연" --review "리뷰 텍스트"
"""

import sys, json, argparse, re
from datetime import date
from pathlib import Path

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
    "초과근무 급여 미지급",
]

WEIGHT = 100 / len(CRITERIA_KEYS)  # 항목당 12.5점


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


def validate_criteria_flags(flags: dict) -> dict:
    """누락된 항목은 false로, 알 수 없는 키는 무시한다."""
    return {k: bool(flags.get(k, False)) for k in CRITERIA_KEYS}


def recalculate_score(agg: dict) -> int:
    n = agg["review_count"]
    if n == 0:
        return 100
    deduction = sum(
        (agg["criteria_violation_counts"][k] / n) * WEIGHT
        for k in CRITERIA_KEYS
    )
    return max(0, round(100 - deduction))


def add_review(business: dict, criteria_flags: dict, review_text: str) -> dict:
    flags = validate_criteria_flags(criteria_flags)

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
        criteria_flags = data.get("criteria_flags", {})
        review_text = data.get("review_text", "")
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
        parser.add_argument(
            "--violations", nargs="*", default=[],
            metavar="항목명",
            help="위반 항목 목록 (예: --violations '휴게시간 부족' '급여지급 지연')",
        )
        parser.add_argument("--review", default="", help="주관식 후기 텍스트 (선택)")
        args = parser.parse_args()

        criteria_flags = {k: (k in args.violations) for k in CRITERIA_KEYS}
        review_text = args.review

        if args.name:
            business_id = slugify(args.name)
            business = load_business(business_id) or new_business(
                business_id, args.name,
                args.area or "미지정",
                args.industry or "기타",
            )
        elif args.positional:
            business_id = args.positional[0]
            business = load_business(business_id)
            if not business:
                print(json.dumps(
                    {"error": f"'{business_id}' 사업장 없음. --name --area --industry 옵션으로 신규 등록하세요."},
                    ensure_ascii=False,
                ))
                sys.exit(1)
        else:
            print(json.dumps(
                {"error": "사용법: add_review.py <business_id> 또는 --name '업체명' --area 지역 --industry 업종"},
                ensure_ascii=False,
            ))
            sys.exit(1)

    result = add_review(business, criteria_flags, review_text)
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
