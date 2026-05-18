package com.cnu.cleanalba.config;

import com.cnu.cleanalba.domain.AnswerOption;
import com.cnu.cleanalba.domain.JobPosting;
import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.Workplace;
import com.cnu.cleanalba.repository.JobPostingRepository;
import com.cnu.cleanalba.repository.ReviewRepository;
import com.cnu.cleanalba.repository.WorkplaceRepository;
import com.cnu.cleanalba.service.CleanScoreService;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.LocalDateTime;
import java.util.List;

@Configuration
@RequiredArgsConstructor
public class SampleDataInitializer {

    private final CleanScoreService cleanScoreService;

    @Bean
    CommandLineRunner loadSampleData(
            WorkplaceRepository workplaceRepository,
            ReviewRepository reviewRepository,
            JobPostingRepository jobPostingRepository
    ) {
        return args -> {
            Workplace frontCafe = new Workplace("전남대 정문 카페 A", "광주 북구 용봉로 전남대 정문 인근", "카페", 35.1769, 126.9082, "정문 근처 테이크아웃 중심 카페");
            Workplace backStore = new Workplace("전남대 후문 편의점 B", "광주 북구 우치로 후문 상권", "편의점", 35.1796, 126.9124, "후문 상권 24시간 편의점");
            Workplace businessRestaurant = new Workplace("상대 식당 C", "광주 북구 상대 인근 먹자골목", "식당", 35.1747, 126.9097, "점심 피크가 뚜렷한 식당");
            Workplace artCafe = new Workplace("예대 근처 카페 D", "광주 북구 예술대학 인근", "카페", 35.1778, 126.9044, "예대 학생 방문이 많은 카페");
            Workplace intersectionRestaurant = new Workplace("후문 사거리 식당 E", "광주 북구 후문 사거리 주변", "식당", 35.1812, 126.9069, "야간 아르바이트 공고가 종종 올라오는 식당");

            workplaceRepository.saveAll(List.of(frontCafe, backStore, businessRestaurant, artCafe, intersectionRestaurant));

            Review r1 = review(frontCafe, "2026.01-2026.03", "주말 파트타임", true, true, AnswerOption.YES, AnswerOption.YES, false, false, false, true, "계약서와 급여 안내가 명확했습니다.", "front-cafe-proof.pdf");
            r1.approve();
            Review r2 = review(frontCafe, "2025.11-2026.01", "평일 마감", true, true, AnswerOption.NOT_APPLICABLE, AnswerOption.YES, false, false, false, true, "마감 업무가 바쁘지만 휴게시간은 지켜졌습니다.", "front-cafe-transfer.png");
            r2.approve();

            Review r3 = review(backStore, "2026.02-2026.04", "야간", false, true, AnswerOption.NO, AnswerOption.NO, true, true, false, false, "검토가 필요한 주관식 내용입니다.", "back-store-chat.jpg");

            Review r4 = review(businessRestaurant, "2025.12-2026.02", "평일 점심", true, true, AnswerOption.YES, AnswerOption.NOT_APPLICABLE, false, true, false, true, "피크 시간 추가 업무가 많았습니다.", "restaurant-contract.pdf");
            r4.approve();

            Review r5 = review(artCafe, "2026.03", "단기", true, false, AnswerOption.NO, AnswerOption.YES, true, false, true, false, "관리자 검토 전에는 공개되지 않는 후기입니다.", "art-cafe-proof.png");

            Review r6 = review(intersectionRestaurant, "2026.01-2026.04", "주말 오전", false, true, AnswerOption.NO, AnswerOption.NO, true, true, true, false, "체크리스트 기준으로 위험 신호가 많았습니다.", "intersection-pay.png");
            r6.approve();

            reviewRepository.saveAll(List.of(r1, r2, r3, r4, r5, r6));

            jobPostingRepository.saveAll(List.of(
                    new JobPosting(frontCafe, "주말 바리스타 모집", "샘플 공고", LocalDateTime.now().minusDays(8)),
                    new JobPosting(backStore, "야간 스태프 모집", "샘플 공고", LocalDateTime.now().minusDays(3)),
                    new JobPosting(backStore, "주말 오후 스태프 모집", "샘플 공고", LocalDateTime.now().minusDays(12)),
                    new JobPosting(intersectionRestaurant, "오픈 주방 단기 알바", "샘플 공고", LocalDateTime.now().minusDays(2)),
                    new JobPosting(intersectionRestaurant, "주방 보조 모집", "샘플 공고", LocalDateTime.now().minusDays(10)),
                    new JobPosting(intersectionRestaurant, "마감 파트 모집", "샘플 공고", LocalDateTime.now().minusDays(22)),
                    new JobPosting(artCafe, "평일 오픈 파트 모집", "샘플 공고", LocalDateTime.now().minusDays(45))
            ));
        };
    }

    private Review review(
            Workplace workplace,
            String workPeriod,
            String employmentType,
            boolean hasWrittenContract,
            boolean followsMinimumWage,
            AnswerOption weeklyPay,
            AnswerOption breakTime,
            boolean delayedPayment,
            boolean unfairExtraWork,
            boolean verbalAbuse,
            boolean recommends,
            String comment,
            String proofFileName
    ) {
        int score = cleanScoreService.calculateReviewScore(
                hasWrittenContract,
                followsMinimumWage,
                weeklyPay,
                breakTime,
                delayedPayment,
                unfairExtraWork,
                verbalAbuse
        );
        return new Review(workplace, workPeriod, employmentType, hasWrittenContract, followsMinimumWage, weeklyPay, breakTime,
                delayedPayment, unfairExtraWork, verbalAbuse, recommends, comment, proofFileName, score);
    }
}
