package com.cnu.cleanalba.dto;

import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.Workplace;

import java.util.List;

public record WorkplaceDetailDto(
        Workplace workplace,
        Double cleanScore,
        String markerColor,
        long approvedReviewCount,
        long recentJobPostingCount,
        boolean frequentJobPosting,
        List<ChecklistStatDto> checklistStats,
        List<Review> approvedReviews
) {
}
