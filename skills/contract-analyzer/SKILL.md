---
name: contract-analyzer
description: 근로계약서 이미지/PDF를 분석하여 핵심 항목을 추출하고 법적 준수 여부를 검증하는 AI Skill. 근로계약서 사진이나 파일을 올리면 자동으로 시급·휴게시간·주휴수당 등 핵심 내용을 파악하고 최저시급 미준수·휴게시간 부족 등 위반 사항을 탐지한다. "계약서 분석해줘", "이 계약서 문제없어?", "최저시급 맞는지 확인해줘", "근로계약서 업로드" 같은 표현이 나오면 즉시 실행한다.
---

# 근로계약서 분석 스킬 (contract-analyzer)

Upstage Document Parse API로 근로계약서를 텍스트화하고, Solar LLM으로 핵심 항목을 추출한 뒤 9개 클린지수 기준 대비 준수 여부를 반환한다.

## 처리 파이프라인

```
계약서 이미지/PDF
    ↓
Document Parse API  (레이아웃 인식 OCR)
    ↓  Markdown 텍스트
Solar Chat API      (구조화 엔티티 추출)
    ↓  extracted_info JSON
준수 여부 검증      (프로그래매틱 + 법적 기준 비교)
    ↓
결과 JSON 반환
```

## 실행 방법

`./scripts/analyze_contract.py`를 실행한다. `UPSTAGE_API_KEY` 환경변수가 필요하다.

```bash
# 일반 PDF/이미지 (텍스트 레이어 있는 경우)
python ./scripts/analyze_contract.py ./contract.pdf

# 스캔 이미지 (OCR 강제 적용)
python ./scripts/analyze_contract.py ./contract_scan.jpg --force-ocr

# stdin JSON 입력
echo '{"file_path": "./contract.jpg", "force_ocr": true}' | python ./scripts/analyze_contract.py
```

## 입력

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `file_path` | string | 필수 | 계약서 이미지 또는 PDF 경로 |
| `force_ocr` | boolean | 선택 | 스캔 문서에 OCR 강제 적용 (기본: false) |

**지원 형식**: PDF, JPEG, PNG, BMP, TIFF, HEIC, DOCX, HWP, HWPX

## 출력 형식

```json
{
  "file": "./assets/recent_contract.png",
  "extracted_info": {
    "business_name": "카페 봄봄",
    "hourly_wage": 10500,
    "monthly_wage": null,
    "work_start_date": "2026-03-01",
    "work_end_date": null,
    "contract_duration_months": null,
    "daily_work_hours": 8.0,
    "weekly_hours": 40.0,
    "break_time_minutes": 60,
    "pay_date": "매월 25일",
    "weekly_holiday_pay_mentioned": true,
    "overtime_pay_mentioned": false,
    "probation_period_exists": false,
    "probation_wage_rate": null,
    "contract_signed_by_both": true,
    "has_illegal_penalty": false,
    "penalty_evidence": null
  },
  "compliance_check": {
    "최저시급_준수": true,
    "휴게시간_준수": true,
    "주휴수당_명시": true,
    "수습기간_합법성": true,
    "독소조항_없음": true
  },
  "confirmed_violations": [],
  "needs_verification": [
    "실제 주휴수당 지급 여부",
    "실제 초과근무 발생 및 수당 지급 여부"
  ],
  "risk_level": "SAFE",
  "minimum_wage_2026": 10030
}
```

## compliance_check 값 의미

| 값 | 의미 |
|---|---|
| `false` | 위반 없음 (준수 확인) |
| `true` | 위반 감지 |
| `null` | 계약서만으로 판단 불가 — 실제 근무 후 리뷰로 확인 필요 |

## 계약서에서 검증 가능한 항목

| 항목 | 검증 방법 |
|---|---|
| 근로계약서 미작성 | 양측 서명·날인 여부 |
| 최저시급 미준수 | 추출된 시급 vs 2026년 최저시급 (10,030원) |
| 주휴수당 미지급 | 계약서 내 주휴수당 언급 여부 |
| 휴게시간 부족 | 근기법 제54조 기준 (4h→30분, 8h→1시간) |
| 초과근무 급여 미지급 | 계약서 내 연장근무 수당 언급 여부 |

## 리스크 등급

| 등급 | 기준 |
|---|---|
| HIGH | 근로계약서 미작성 또는 최저시급 미준수 감지 |
| MEDIUM | 확인된 위반 항목 2개 이상 |
| LOW | 확인된 위반 항목 1개 |
| SAFE | 확인된 위반 없음 |

## 클린알바맵 연동 시나리오

1. 알바생이 근로계약서 사진 업로드
2. `contract-analyzer` → 시급·휴게시간 등 추출 + 위반 항목 탐지
3. O/X 체크리스트 항목과 교차 검증 (예: 알바생이 "최저시급 준수"로 체크했는데 계약서 시급이 최저시급 미만이면 불일치 플래그)
4. 결과를 `add_review.py`에 전달하여 클린지수 산출에 반영

## 예시 파일

데모 및 테스트용 샘플 근로계약서 이미지: `./assets/recent_contract.png`

```bash
python ./scripts/analyze_contract.py ./assets/recent_contract.png
```

## 환경 설정

`UPSTAGE_API_KEY` 환경변수가 설정되어 있어야 한다. `.env.example` 참고: `./assets/.env.example`
