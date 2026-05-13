#!/usr/bin/env python3
"""
review_purify_skill — 알바 후기 법적 순화 스크립트
Upstage Solar Chat API를 사용하여 주관식 후기를 법적으로 안전한 표현으로 순화한다.

사용법:
    python purify.py "사장 성질 더럽고 월급도 맨날 늦게 줌"
    echo '{"review_text": "..."}' | python purify.py
"""

import os
import sys
import json
from openai import OpenAI

UPSTAGE_API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    print(json.dumps({"error": "UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다."}))
    sys.exit(1)

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1",
)

SYSTEM_PROMPT = """당신은 알바 후기 법적 안전성 검토 전문가입니다.
한국 근로기준법과 명예훼손 관련 법률(형법 제307조, 정보통신망법 제44조의7)을 기반으로 입력 텍스트를 분석하고 순화하세요.

핵심 원칙: 사람의 성격·인성·태도·말투를 직접 평가하는 표현은 사용하지 않는다.
대신 근무자가 실제로 경험한 상황이나 업무 환경 중심으로 서술한다.

예시:
- ❌ "관리자의 감정적 언행이 있을 수 있음" (사람 평가)
- ✅ "고성이 오가는 상황이 발생한 적 있음" (경험한 상황 중심)
- ❌ "고용주와의 소통이 원활하지 않을 수 있음" (사람 평가)
- ✅ "급여 지급일이 반복적으로 지연된 경험이 있음" (업무 환경 중심)

다음 기준으로 처리하세요:
1. 명예훼손 소지 표현(특정인 지칭 모욕, 검증 불가 사실 단정) 탐지 및 순화
2. 욕설·혐오 표현 제거 후 근무자가 겪은 상황·환경 중심 표현으로 대체
3. 법적 단정 표현('위법이다', '처벌받아야 한다' 등)을 중립 표현으로 변환
4. 허위 가능성 있는 단정적 서술을 가능성 표현으로 완화
5. 원래 의미(사실 내용)가 손상되지 않도록 유지
6. 순화 이유를 사용자 친화적으로 설명 (관련 법 조항 포함)

리스크 등급 기준:
- HIGH: 명예훼손 소송 위험이 높은 표현 포함
- MEDIUM: 욕설·감정 표현이 포함되어 삭제 위험 있음
- LOW: 경미한 주관적 표현, 권고 수준의 순화
- SAFE: 법적 문제 없음, 순화 불필요

항상 한국어로 응답하세요."""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "purify_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "purified_text": {
                    "type": "string",
                    "description": "법적으로 안전하게 순화된 후기 텍스트"
                },
                "risk_level": {
                    "type": "string",
                    "description": "리스크 등급: HIGH, MEDIUM, LOW, SAFE 중 하나"
                },
                "extracted_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "후기에서 추출된 근무환경 태그 (예: 급여지연, 소통어려움)"
                },
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "original": {"type": "string", "description": "원문 표현"},
                            "replaced": {"type": "string", "description": "순화된 표현"},
                            "reason": {"type": "string", "description": "순화 이유 및 관련 법 조항"}
                        },
                        "required": ["original", "replaced", "reason"],
                        "additionalProperties": False
                    },
                    "description": "변경 사항 목록"
                }
            },
            "required": ["purified_text", "risk_level", "extracted_tags", "changes"],
            "additionalProperties": False
        }
    }
}


def purify_review(review_text: str) -> dict:
    response = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 알바 후기를 분석하고 순화해주세요:\n\n{review_text}"}
        ],
        response_format=RESPONSE_SCHEMA,
        temperature=0.3,
        max_tokens=1024,
    )
    return json.loads(response.choices[0].message.content)


def main():
    # stdin에서 JSON 입력 처리
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        try:
            data = json.loads(raw)
            review_text = data.get("review_text", "")
        except json.JSONDecodeError:
            review_text = raw
    # 커맨드라인 인수 처리
    elif len(sys.argv) > 1:
        review_text = " ".join(sys.argv[1:])
    else:
        print(json.dumps({"error": "후기 텍스트를 입력해주세요."}, ensure_ascii=False))
        sys.exit(1)

    if not review_text.strip():
        print(json.dumps({"error": "빈 텍스트는 처리할 수 없습니다."}, ensure_ascii=False))
        sys.exit(1)

    result = purify_review(review_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
