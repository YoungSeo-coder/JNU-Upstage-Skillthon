package com.cnu.cleanalba.repository;

import com.cnu.cleanalba.domain.Review;
import com.cnu.cleanalba.domain.ReviewStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ReviewRepository extends JpaRepository<Review, Long> {

    List<Review> findByWorkplaceIdAndStatusOrderByCreatedAtDesc(Long workplaceId, ReviewStatus status);

    List<Review> findByStatusOrderByCreatedAtAsc(ReviewStatus status);

    long countByWorkplaceIdAndStatus(Long workplaceId, ReviewStatus status);
}
