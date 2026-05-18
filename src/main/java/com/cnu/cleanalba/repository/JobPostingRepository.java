package com.cnu.cleanalba.repository;

import com.cnu.cleanalba.domain.JobPosting;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;

public interface JobPostingRepository extends JpaRepository<JobPosting, Long> {

    long countByWorkplaceIdAndPostedAtAfter(Long workplaceId, LocalDateTime postedAfter);

    List<JobPosting> findByWorkplaceIdOrderByPostedAtDesc(Long workplaceId);
}
