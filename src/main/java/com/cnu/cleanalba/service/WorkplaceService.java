package com.cnu.cleanalba.service;

import com.cnu.cleanalba.domain.AnswerOption;
import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.ReviewStatus;
import com.cnu.cleanalba.domain.Workplace;
import com.cnu.cleanalba.dto.ChecklistStatDto;
import com.cnu.cleanalba.dto.MapWorkplaceDto;
import com.cnu.cleanalba.dto.WorkplaceDetailDto;
import com.cnu.cleanalba.dto.WorkplaceSummaryDto;
import com.cnu.cleanalba.repository.ReviewRepository;
import com.cnu.cleanalba.repository.WorkplaceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class WorkplaceService {

    private final WorkplaceRepository workplaceRepository;
    private final ReviewRepository reviewRepository;
    private final CleanScoreService cleanScoreService;
    private final JobPostingService jobPostingService;

    public List<WorkplaceSummaryDto> getWorkplaceSummaries() {
        return workplaceRepository.findAll().stream()
                .map(this::toSummary)
                .toList();
    }

    public List<MapWorkplaceDto> getMapWorkplaces() {
        return workplaceRepository.findAll().stream()
                .map(workplace -> {
                    Double score = cleanScoreService.calculateAverageScore(workplace.getId());
                    long count = reviewRepository.countByWorkplaceIdAndStatus(workplace.getId(), ReviewStatus.APPROVED);
                    return new MapWorkplaceDto(
                            workplace.getId(),
                            workplace.getName(),
                            workplace.getAddress(),
                            workplace.getLatitude(),
                            workplace.getLongitude(),
                            score,
                            count,
                            cleanScoreService.getMarkerColor(score, count)
                    );
                })
                .toList();
    }

    public Workplace findById(Long id) {
        return workplaceRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("사업장을 찾을 수 없습니다. id=" + id));
    }

    public WorkplaceDetailDto getDetail(Long workplaceId) {
        Workplace workplace = findById(workplaceId);
        List<Review> approvedReviews = reviewRepository.findByWorkplaceIdAndStatusOrderByCreatedAtDesc(workplaceId, ReviewStatus.APPROVED);
        Double score = cleanScoreService.calculateAverageScore(workplaceId);
        long reviewCount = approvedReviews.size();
        return new WorkplaceDetailDto(
                workplace,
                score,
                cleanScoreService.getMarkerColor(score, reviewCount),
                reviewCount,
                jobPostingService.countRecentPostings(workplaceId),
                jobPostingService.isFrequentPosting(workplaceId),
                buildChecklistStats(approvedReviews),
                approvedReviews
        );
    }

    private WorkplaceSummaryDto toSummary(Workplace workplace) {
        Double score = cleanScoreService.calculateAverageScore(workplace.getId());
        long reviewCount = reviewRepository.countByWorkplaceIdAndStatus(workplace.getId(), ReviewStatus.APPROVED);
        long recentPostings = jobPostingService.countRecentPostings(workplace.getId());
        return new WorkplaceSummaryDto(
                workplace.getId(),
                workplace.getName(),
                workplace.getAddress(),
                workplace.getCategory(),
                score,
                reviewCount,
                recentPostings,
                recentPostings >= 3,
                cleanScoreService.getMarkerColor(score, reviewCount)
        );
    }

    private List<ChecklistStatDto> buildChecklistStats(List<Review> reviews) {
        return List.of(
                booleanStat("근로계약서 작성", reviews.stream().filter(Review::isHasWrittenContract).count(), reviews.size()),
                booleanStat("최저시급 준수", reviews.stream().filter(Review::isFollowsMinimumWage).count(), reviews.size()),
                optionStat("주휴수당 지급", reviews.stream().map(Review::getReceivesWeeklyHolidayPay).toList()),
                optionStat("휴게시간 보장", reviews.stream().map(Review::getHasBreakTime).toList()),
                negativeFlagStat("임금 지급 지연 없음", reviews.stream().filter(Review::isHasDelayedPayment).count(), reviews.size()),
                negativeFlagStat("부당한 추가 업무 없음", reviews.stream().filter(Review::isHasUnfairExtraWork).count(), reviews.size()),
                negativeFlagStat("폭언/폭행 경험 없음", reviews.stream().filter(Review::isHasVerbalAbuse).count(), reviews.size())
        );
    }

    private ChecklistStatDto booleanStat(String label, long yesCount, long total) {
        return new ChecklistStatDto(label, yesCount, total - yesCount, 0);
    }

    private ChecklistStatDto negativeFlagStat(String label, long badCount, long total) {
        return new ChecklistStatDto(label, total - badCount, badCount, 0);
    }

    private ChecklistStatDto optionStat(String label, List<AnswerOption> options) {
        long yes = options.stream().filter(option -> option == AnswerOption.YES).count();
        long no = options.stream().filter(option -> option == AnswerOption.NO).count();
        long na = options.stream().filter(option -> option == AnswerOption.NOT_APPLICABLE).count();
        return new ChecklistStatDto(label, yes, no, na);
    }
}
