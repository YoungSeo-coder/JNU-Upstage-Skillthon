package com.cnu.cleanalba.service;

import com.cnu.cleanalba.repository.JobPostingRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class JobPostingService {

    private static final int FREQUENT_POSTING_THRESHOLD = 3;

    private final JobPostingRepository jobPostingRepository;

    public long countRecentPostings(Long workplaceId) {
        return jobPostingRepository.countByWorkplaceIdAndPostedAtAfter(workplaceId, LocalDateTime.now().minusDays(30));
    }

    public boolean isFrequentPosting(Long workplaceId) {
        return countRecentPostings(workplaceId) >= FREQUENT_POSTING_THRESHOLD;
    }
}
