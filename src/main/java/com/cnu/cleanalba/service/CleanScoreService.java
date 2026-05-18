package com.cnu.cleanalba.service;

import com.cnu.cleanalba.domain.AnswerOption;
import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.ReviewStatus;
import com.cnu.cleanalba.repository.ReviewRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CleanScoreService {

    private final ReviewRepository reviewRepository;

    public int calculateReviewScore(
            boolean hasWrittenContract,
            boolean followsMinimumWage,
            AnswerOption receivesWeeklyHolidayPay,
            AnswerOption hasBreakTime,
            boolean hasDelayedPayment,
            boolean hasUnfairExtraWork,
            boolean hasVerbalAbuse
    ) {
        int score = 0;
        if (hasWrittenContract) {
            score += 20;
        }
        if (followsMinimumWage) {
            score += 20;
        }
        if (receivesWeeklyHolidayPay == AnswerOption.YES || receivesWeeklyHolidayPay == AnswerOption.NOT_APPLICABLE) {
            score += 15;
        }
        if (hasBreakTime == AnswerOption.YES || hasBreakTime == AnswerOption.NOT_APPLICABLE) {
            score += 15;
        }
        if (!hasDelayedPayment) {
            score += 15;
        }
        if (!hasUnfairExtraWork) {
            score += 10;
        }
        if (!hasVerbalAbuse) {
            score += 5;
        }
        return Math.min(score, 100);
    }

    public Double calculateAverageScore(Long workplaceId) {
        List<Review> reviews = reviewRepository.findByWorkplaceIdAndStatusOrderByCreatedAtDesc(workplaceId, ReviewStatus.APPROVED);
        if (reviews.isEmpty()) {
            return null;
        }
        return reviews.stream()
                .mapToInt(Review::getCalculatedScore)
                .average()
                .orElse(0);
    }

    public String getMarkerColor(Double score, long approvedReviewCount) {
        if (score == null || approvedReviewCount == 0) {
            return "gray";
        }
        if (score >= 80) {
            return "green";
        }
        if (score >= 60) {
            return "yellow";
        }
        if (score >= 40) {
            return "orange";
        }
        return "red";
    }
}
