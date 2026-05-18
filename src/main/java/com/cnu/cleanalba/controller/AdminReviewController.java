package com.cnu.cleanalba.controller;

import com.cnu.cleanalba.service.ReviewService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequiredArgsConstructor
@RequestMapping("/admin/reviews")
public class AdminReviewController {

    private final ReviewService reviewService;

    // TODO: MVP 이후 Spring Security로 관리자 인증/인가를 붙이세요.
    @GetMapping
    public String pendingReviews(Model model) {
        model.addAttribute("reviews", reviewService.getPendingReviews());
        return "admin/reviews";
    }

    @GetMapping("/{id}")
    public String detail(@PathVariable Long id, Model model) {
        model.addAttribute("review", reviewService.findById(id));
        return "admin/review-detail";
    }

    @PostMapping("/{id}/approve")
    public String approve(@PathVariable Long id) {
        reviewService.approve(id);
        return "redirect:/admin/reviews";
    }

    @PostMapping("/{id}/reject")
    public String reject(@PathVariable Long id) {
        reviewService.reject(id);
        return "redirect:/admin/reviews";
    }
}
