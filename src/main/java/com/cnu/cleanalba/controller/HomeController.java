package com.cnu.cleanalba.controller;

import com.cnu.cleanalba.service.WorkplaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@RequiredArgsConstructor
public class HomeController {

    private final WorkplaceService workplaceService;

    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("workplaces", workplaceService.getWorkplaceSummaries());
        return "index";
    }

    @GetMapping("/about")
    public String about() {
        return "about";
    }
}
