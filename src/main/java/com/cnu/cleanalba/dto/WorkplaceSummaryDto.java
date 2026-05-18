package com.cnu.cleanalba.dto;

public record WorkplaceSummaryDto(
        Long id,
        String name,
        String address,
        String category,
        Double cleanScore,
        long reviewCount,
        long recentJobPostingCount,
        boolean frequentJobPosting,
        String markerColor
) {
    public String scoreLabel() {
        return cleanScore == null ? "후기 부족" : Math.round(cleanScore) + "점";
    }
}
