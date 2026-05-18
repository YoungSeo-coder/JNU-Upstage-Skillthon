package com.cnu.cleanalba.controller;

import com.cnu.cleanalba.domain.AnswerOption;
import com.cnu.cleanalba.dto.ReviewForm;
import com.cnu.cleanalba.service.ReviewService;
import com.cnu.cleanalba.service.WorkplaceService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;
    private final WorkplaceService workplaceService;

    @GetMapping("/reviews/new")
    public String newReview(@RequestParam(required = false) Long workplaceId, Model model) {
        ReviewForm form = new ReviewForm();
        form.setWorkplaceId(workplaceId);
        prepareForm(model, form);
        return "reviews/new";
    }

    @PostMapping("/reviews")
    public String create(
            @Valid @ModelAttribute("reviewForm") ReviewForm reviewForm,
            BindingResult bindingResult,
            Model model,
            RedirectAttributes redirectAttributes
    ) {
        if (reviewForm.getProofFile() == null || reviewForm.getProofFile().isEmpty()) {
            bindingResult.rejectValue("proofFile", "required", "근로 인증 자료를 업로드해 주세요.");
        }

        if (bindingResult.hasErrors()) {
            prepareForm(model, reviewForm);
            return "reviews/new";
        }

        reviewService.createReview(reviewForm);
        redirectAttributes.addFlashAttribute("message", "후기가 접수되었습니다. 관리자 검수 후 공개 반영됩니다.");
        return "redirect:/workplaces/" + reviewForm.getWorkplaceId();
    }

    private void prepareForm(Model model, ReviewForm reviewForm) {
        model.addAttribute("reviewForm", reviewForm);
        model.addAttribute("workplaces", workplaceService.getWorkplaceSummaries());
        model.addAttribute("answerOptions", AnswerOption.values());
    }
}
