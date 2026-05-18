package com.cnu.cleanalba.dto;

public record ChecklistStatDto(
        String label,
        long positiveCount,
        long negativeCount,
        long notApplicableCount
) {
}
