package com.cnu.cleanalba.dto;

import com.cnu.cleanalba.domain.AnswerOption;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;
import org.springframework.web.multipart.MultipartFile;

@Getter
@Setter
public class ReviewForm {

    @NotNull(message = "사업장을 선택해 주세요.")
    private Long workplaceId;

    @NotBlank(message = "근무 기간을 입력해 주세요.")
    private String workPeriod;

    @NotBlank(message = "근무 형태를 입력해 주세요.")
    private String employmentType;

    @NotNull(message = "근로계약서 작성 여부를 선택해 주세요.")
    private Boolean hasWrittenContract;

    @NotNull(message = "최저시급 준수 여부를 선택해 주세요.")
    private Boolean followsMinimumWage;

    @NotNull(message = "주휴수당 지급 여부를 선택해 주세요.")
    private AnswerOption receivesWeeklyHolidayPay;

    @NotNull(message = "휴게시간 보장 여부를 선택해 주세요.")
    private AnswerOption hasBreakTime;

    @NotNull(message = "임금 지급 지연 여부를 선택해 주세요.")
    private Boolean hasDelayedPayment;

    @NotNull(message = "부당한 추가 업무 요구 여부를 선택해 주세요.")
    private Boolean hasUnfairExtraWork;

    @NotNull(message = "욕설/폭언 경험 여부를 선택해 주세요.")
    private Boolean hasVerbalAbuse;

    @NotNull(message = "전반적인 근무 추천 여부를 선택해 주세요.")
    private Boolean recommendsWorkplace;

    @Size(max = 2000, message = "주관식 후기는 2000자 이하로 입력해 주세요.")
    private String subjectiveComment;

    private MultipartFile proofFile;
}
