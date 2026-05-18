package com.cnu.cleanalba.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Review {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "workplace_id")
    private Workplace workplace;

    @Column(nullable = false)
    private String workPeriod;

    @Column(nullable = false)
    private String employmentType;

    @Column(nullable = false)
    private boolean hasWrittenContract;

    @Column(nullable = false)
    private boolean followsMinimumWage;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AnswerOption receivesWeeklyHolidayPay;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AnswerOption hasBreakTime;

    @Column(nullable = false)
    private boolean hasDelayedPayment;

    @Column(nullable = false)
    private boolean hasUnfairExtraWork;

    @Column(nullable = false)
    private boolean hasVerbalAbuse;

    @Column(nullable = false)
    private boolean recommendsWorkplace;

    @Column(length = 2000)
    private String subjectiveComment;

    @Column(nullable = false)
    private String proofFileName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ReviewStatus status;

    @Column(nullable = false)
    private int calculatedScore;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    public Review(
            Workplace workplace,
            String workPeriod,
            String employmentType,
            boolean hasWrittenContract,
            boolean followsMinimumWage,
            AnswerOption receivesWeeklyHolidayPay,
            AnswerOption hasBreakTime,
            boolean hasDelayedPayment,
            boolean hasUnfairExtraWork,
            boolean hasVerbalAbuse,
            boolean recommendsWorkplace,
            String subjectiveComment,
            String proofFileName,
            int calculatedScore
    ) {
        this.workplace = workplace;
        this.workPeriod = workPeriod;
        this.employmentType = employmentType;
        this.hasWrittenContract = hasWrittenContract;
        this.followsMinimumWage = followsMinimumWage;
        this.receivesWeeklyHolidayPay = receivesWeeklyHolidayPay;
        this.hasBreakTime = hasBreakTime;
        this.hasDelayedPayment = hasDelayedPayment;
        this.hasUnfairExtraWork = hasUnfairExtraWork;
        this.hasVerbalAbuse = hasVerbalAbuse;
        this.recommendsWorkplace = recommendsWorkplace;
        this.subjectiveComment = subjectiveComment;
        this.proofFileName = proofFileName;
        this.status = ReviewStatus.PENDING;
        this.calculatedScore = calculatedScore;
        this.createdAt = LocalDateTime.now();
    }

    public void approve() {
        this.status = ReviewStatus.APPROVED;
    }

    public void reject() {
        this.status = ReviewStatus.REJECTED;
    }
}
