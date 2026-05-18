package com.cnu.cleanalba.service;

import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.ReviewStatus;
import com.cnu.cleanalba.domain.Workplace;
import com.cnu.cleanalba.dto.ReviewForm;
import com.cnu.cleanalba.repository.ReviewRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ReviewService {

    private final ReviewRepository reviewRepository;
    private final WorkplaceService workplaceService;
    private final CleanScoreService cleanScoreService;

    @Transactional
    public Review createReview(ReviewForm form) {
        Workplace workplace = workplaceService.findById(form.getWorkplaceId());
        String proofFileName = StringUtils.cleanPath(form.getProofFile().getOriginalFilename());

        int score = cleanScoreService.calculateReviewScore(
                form.getHasWrittenContract(),
                form.getFollowsMinimumWage(),
                form.getReceivesWeeklyHolidayPay(),
                form.getHasBreakTime(),
                form.getHasDelayedPayment(),
                form.getHasUnfairExtraWork(),
                form.getHasVerbalAbuse()
        );

        // MVP 정책: 인증 자료 원본은 공개하지 않고 관리자 검수용 파일명만 저장합니다.
        Review review = new Review(
                workplace,
                form.getWorkPeriod(),
                form.getEmploymentType(),
                form.getHasWrittenContract(),
                form.getFollowsMinimumWage(),
                form.getReceivesWeeklyHolidayPay(),
                form.getHasBreakTime(),
                form.getHasDelayedPayment(),
                form.getHasUnfairExtraWork(),
                form.getHasVerbalAbuse(),
                form.getRecommendsWorkplace(),
                form.getSubjectiveComment(),
                proofFileName,
                score
        );
        return reviewRepository.save(review);
    }

    @Transactional(readOnly = true)
    public List<Review> getPendingReviews() {
        return reviewRepository.findByStatusOrderByCreatedAtAsc(ReviewStatus.PENDING);
    }

    @Transactional(readOnly = true)
    public Review findById(Long id) {
        return reviewRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("후기를 찾을 수 없습니다. id=" + id));
    }

    @Transactional
    public void approve(Long id) {
        findById(id).approve();
    }

    @Transactional
    public void reject(Long id) {
        findById(id).reject();
    }
}
