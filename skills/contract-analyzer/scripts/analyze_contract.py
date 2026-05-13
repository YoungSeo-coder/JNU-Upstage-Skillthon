#!/usr/bin/env python3
"""
analyze_contract.py — 근로계약서 분석 및 법적 준수 여부 검증

Upstage Document Parse API로 계약서 이미지/PDF를 텍스트화한 뒤,
Solar Chat API로 핵심 항목을 추출하고 9개 클린지수 기준 대비 준수 여부를 반환한다.

사용법:
    python analyze_contract.py ./contract.jpg
    python analyze_contract.py ./contract.pdf --force-ocr
    echo '{"file_path": "./contract.jpg"}' | python analyze_contract.py
"""

import os, sys, json, argparse
from pathlib import Path
import requests
from openai import OpenAI

UPSTAGE_API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    print(json.dumps({"error": "UPSTAGE_API_KEY 환경변수가 설정되지 않았습니다."}, ensure_ascii=False))
    sys.exit(1)

client = OpenAI(api_key=UPSTAGE_API_KEY, base_url="https://api.upstage.ai/v1")

PARSE_ENDPOINT = "https://api.upstage.ai/v1/document-digitization"

# 2026년 한국 최저시급 (고용노동부 고시 기준 — 변경 시 업데이트 필요)
MIN_HOURLY_WAGE_2026 = 10030

# ── 스키마 ──────────────────────────────────────────────────────────────

EXTRACT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "contract_entities",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "business_name": {
                    "type": ["string", "null"],
                    "description": "사업장 상호명",
                },
                "hourly_wage": {
                    "type": ["integer", "null"],
                    "description": "시급 (원). 월급만 명시된 경우 null.",
                },
                "monthly_wage": {
                    "type": ["integer", "null"],
                    "description": "월급 (원). 시급만 명시된 경우 null.",
                },
                "work_start_date": {
                    "type": ["string", "null"],
                    "description": "근로 시작일 (YYYY-MM-DD 형식). 미기재 시 null.",
                },
                "work_end_date": {
                    "type": ["string", "null"],
                    "description": "근로 종료일 (YYYY-MM-DD 형식). 기간 미정이면 null.",
                },
                "daily_work_hours": {
                    "type": ["number", "null"],
                    "description": "1일 근로시간 (시간 단위). 미기재 시 null.",
                },
                "weekly_hours": {
                    "type": ["number", "null"],
                    "description": "주당 근로시간 (시간 단위). 미기재 시 null.",
                },
                "break_time_minutes": {
                    "type": ["integer", "null"],
                    "description": "1일 휴게시간 (분 단위). 미기재 시 null.",
                },
                "pay_date": {
                    "type": ["string", "null"],
                    "description": "급여 지급일 (예: '매월 25일'). 미기재 시 null.",
                },
                "weekly_holiday_pay_mentioned": {
                    "type": "boolean",
                    "description": "주휴수당 지급이 계약서에 명시되어 있는지 여부.",
                },
                "overtime_pay_mentioned": {
                    "type": "boolean",
                    "description": "초과근무 수당 지급이 계약서에 명시되어 있는지 여부.",
                },
                "contract_signed_by_both": {
                    "type": "boolean",
                    "description": "사업주와 근로자 양측이 서명·날인했는지 여부.",
                },
                "probation_period_exists": {
                    "type": "boolean",
                    "description": "수습기간 조항이 명시되어 있는지 여부.",
                },
                "probation_wage_rate": {
                    "type": ["number", "null"],
                    "description": "수습기간 급여 비율 (예: 최저임금의 90% → 0.9). 삭감 조항 없으면 null.",
                },
                "contract_duration_months": {
                    "type": ["integer", "null"],
                    "description": "총 근로계약 기간 (개월 수). 기간 미정이거나 명시 없으면 null.",
                },
                "has_illegal_penalty": {
                    "type": "boolean",
                    "description": "근로기준법 제20조 위반 독소 조항(위약금·손해배상 강제·근태 벌금 등) 존재 여부.",
                },
                "penalty_evidence": {
                    "type": ["string", "null"],
                    "description": "위반 조항 발견 시 해당 원문 문장 발췌. 위반 없으면 null.",
                },
            },
            "required": [
                "business_name", "hourly_wage", "monthly_wage",
                "work_start_date", "work_end_date",
                "daily_work_hours", "weekly_hours", "break_time_minutes",
                "pay_date", "weekly_holiday_pay_mentioned",
                "overtime_pay_mentioned", "contract_signed_by_both",
                "probation_period_exists", "probation_wage_rate",
                "contract_duration_months",
                "has_illegal_penalty", "penalty_evidence",
            ],
            "additionalProperties": False,
        },
    },
}

EXTRACT_SYSTEM = """당신은 한국 근로계약서 분석 전문가입니다.
제공된 근로계약서 텍스트에서 아래 항목들을 정확히 추출하세요.
명시되지 않은 항목은 null로 반환하세요.

추출 주의사항:
- 시급: '시간급', '시급', '시간당' 등의 표현과 함께 기재된 금액
- 월급: '월급여', '월 급여', '월 임금' 등의 표현과 함께 기재된 금액
- 휴게시간: 분 단위로 변환 (예: '30분' → 30, '1시간' → 60)
- 주휴수당: 계약서에 '주휴수당', '주휴일', '유급휴일' 등이 언급된 경우 true
- 초과근무 수당: '연장근무수당', '초과수당', '가산임금' 등이 언급된 경우 true
- 양측 서명: 사업주·근로자 모두 서명란 또는 날인이 있는 경우 true
- 수습기간: '수습', '수습기간', '수습기간 중' 등의 조항이 있으면 true
- 수습기간 급여 비율: '수습 중 최저임금의 90%', '수습기간 급여 90%' 등의 삭감 조항에서 비율 추출
  (예: 90% → 0.9, 80% → 0.8). 삭감 조항 없으면 null
- 계약 기간: 근로 시작일~종료일로 계산한 개월 수. '3개월', '6개월', '1년' 등 직접 명시된 경우 우선 사용.
  기간 미정(무기계약 등)이면 null
- 독소 조항(근로기준법 제20조): '벌금', '위약금', '손해배상', '공제', '미지급', '차감' 키워드를 문맥과 함께 분석.
  아래 경우만 위반(has_illegal_penalty=true)으로 판별:
  · 근태 페널티: "지각/결근 시 OOO원 공제", "벌금 OOO원 부과" 등
  · 퇴사 페널티: "무단퇴사 시 급여 미지급", "계약 미이행 시 위약금 배상", "퇴사 시 손해배상 청구" 등
  아래는 정상 조항이므로 위반 아님:
  · 4대 보험료·3.3% 사업소득세 공제
  · 일하지 않은 시간에 대한 무급 처리
  위반 시 penalty_evidence에 해당 원문 문장을 정확히 발췌. 위반 없으면 null.

항상 한국어로 응답하세요."""


# ── Document Parse ──────────────────────────────────────────────────────

def parse_document(file_path: str, force_ocr: bool = False) -> str:
    """Document Parse API로 계약서를 텍스트화한다."""
    form_data = {
        "model": "document-parse",
        "output_formats": '["markdown"]',
        "coordinates": "false",
    }
    if force_ocr:
        form_data["ocr"] = "force"

    with open(file_path, "rb") as f:
        resp = requests.post(
            PARSE_ENDPOINT,
            headers={"Authorization": f"Bearer {UPSTAGE_API_KEY}"},
            files={"document": f},
            data=form_data,
        )
    resp.raise_for_status()
    return resp.json()["content"]["markdown"]


# ── 엔티티 추출 ─────────────────────────────────────────────────────────

def extract_entities(parsed_text: str) -> dict:
    """Solar LLM으로 핵심 항목을 구조화 추출한다."""
    resp = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"다음 근로계약서 텍스트를 분석해주세요:\n\n{parsed_text}"},
        ],
        response_format=EXTRACT_SCHEMA,
        temperature=0.0,
        max_tokens=512,
    )
    return json.loads(resp.choices[0].message.content)


# ── 준수 여부 검증 ──────────────────────────────────────────────────────

def check_compliance(entities: dict) -> dict:
    """
    계약서로 판단 가능한 항목만 검사한다.
    - false: 위반 없음 (준수)
    - true: 위반 감지
    - null: 계약서만으로 판단 불가 (실제 근무 후 리뷰로 확인 필요)
    """
    checks = {}

    # 1. 최저시급 미준수 — 시급이 최저시급보다 낮을 때만 true
    hourly = entities.get("hourly_wage")
    if hourly is not None:
        checks["최저시급 미준수"] = hourly < MIN_HOURLY_WAGE_2026
    else:
        checks["최저시급 미준수"] = None  # 월급제 등: 판단 불가

    # 2. 주휴수당 — 계약서만으로 지급 여부 판단 불가.
    #    주 15시간 이상 근무 시 주휴수당 대상 조건 충족 → 확인 필요 안내
    weekly_h = entities.get("weekly_hours")
    if weekly_h is not None and weekly_h >= 15:
        checks["주휴수당"] = "확인필요"  # 주 15시간 이상: 지급 조건 충족 여부 확인 필요
    else:
        checks["주휴수당"] = None  # 주 15시간 미만이거나 정보 없음: 판단 불가

    # 3. 휴게시간 부족 — 근기법 제54조: 4시간→30분, 8시간→1시간
    daily_h = entities.get("daily_work_hours")
    break_m = entities.get("break_time_minutes")
    if daily_h is not None and break_m is not None:
        if daily_h >= 8:
            checks["휴게시간 부족"] = break_m < 60
        elif daily_h >= 4:
            checks["휴게시간 부족"] = break_m < 30
        else:
            checks["휴게시간 부족"] = False
    else:
        checks["휴게시간 부족"] = None

    # 4. 초과근무 급여 미지급 — 계약서 미언급 시 리스크
    checks["초과근무 급여 미지급"] = not entities.get("overtime_pay_mentioned", False)

    # 9. 최저임금법 수습기간 준수 (최저임금법 제5조 제2항)
    #    수습기간 급여 삭감은 계약기간 1년 이상일 때만 허용
    probation_exists = entities.get("probation_period_exists", False)
    probation_rate = entities.get("probation_wage_rate")
    duration_months = entities.get("contract_duration_months")

    if probation_exists and probation_rate is not None and probation_rate < 1.0:
        # 수습 급여 삭감 조항 존재
        if duration_months is not None:
            # 계약기간이 명시된 경우: 1년(12개월) 미만이면 위반
            checks["수습기간동안 최저임금준수"] = duration_months < 12
        else:
            # 계약기간 불명 (무기계약 등): 판단 불가
            checks["수습기간동안 최저임금준수"] = None
    else:
        # 수습 삭감 조항 없음: 위반 없음
        checks["수습기간동안 최저임금준수"] = False

    # 위약금·손해배상 독소 조항 (근로기준법 제20조)
    checks["위약금_손해배상_강제조항"] = entities.get("has_illegal_penalty", False)

    return checks


def risk_level(checks: dict) -> str:
    confirmed_violations = [k for k, v in checks.items() if v is True]
    if any(k in confirmed_violations for k in ["최저시급 미준수", "수습기간동안 최저임금준수", "위약금_손해배상_강제조항"]):
        return "HIGH"
    if len(confirmed_violations) >= 2:
        return "MEDIUM"
    if confirmed_violations:
        return "LOW"
    return "SAFE"


# ── 메인 ────────────────────────────────────────────────────────────────

def analyze(file_path: str, force_ocr: bool = False) -> dict:
    parsed_text = parse_document(file_path, force_ocr=force_ocr)
    entities = extract_entities(parsed_text)
    checks = check_compliance(entities)

    return {
        "file": file_path,
        "extracted_info": entities,
        "compliance_check": checks,
        "confirmed_violations": [k for k, v in checks.items() if v is True],
        "needs_verification": [k for k, v in checks.items() if v == "확인필요"],
        "unverifiable_items": [k for k, v in checks.items() if v is None],
        "risk_level": risk_level(checks),
        "minimum_wage_2026": MIN_HOURLY_WAGE_2026,
    }


def main():
    if not sys.stdin.isatty():
        data = json.loads(sys.stdin.read().strip())
        file_path = data.get("file_path", "")
        force_ocr = data.get("force_ocr", False)
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("file_path", help="계약서 이미지 또는 PDF 경로")
        parser.add_argument("--force-ocr", action="store_true",
                            help="이미지 기반 스캔 문서에 OCR 강제 적용")
        args = parser.parse_args()
        file_path = args.file_path
        force_ocr = args.force_ocr

    if not file_path or not Path(file_path).exists():
        print(json.dumps(
            {"error": f"파일을 찾을 수 없습니다: {file_path}"},
            ensure_ascii=False,
        ))
        sys.exit(1)

    result = analyze(file_path, force_ocr=force_ocr)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
