package com.cnu.cleanalba.controller;

import com.cnu.cleanalba.service.WorkplaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
@RequiredArgsConstructor
public class WorkplaceController {

    private final WorkplaceService workplaceService;

    @GetMapping("/workplaces")
    public String list(Model model) {
        model.addAttribute("workplaces", workplaceService.getWorkplaceSummaries());
        return "workplaces/list";
    }

    @GetMapping("/workplaces/{id}")
    public String detail(@PathVariable Long id, Model model) {
        model.addAttribute("detail", workplaceService.getDetail(id));
        return "workplaces/detail";
    }
}
