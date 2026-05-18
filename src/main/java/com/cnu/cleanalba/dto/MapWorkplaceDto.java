package com.cnu.cleanalba.dto;

public record MapWorkplaceDto(
        Long id,
        String name,
        String address,
        double latitude,
        double longitude,
        Double cleanScore,
        long reviewCount,
        String markerColor
) {
}
