package com.cnu.cleanalba.controller;

import com.cnu.cleanalba.dto.MapWorkplaceDto;
import com.cnu.cleanalba.service.WorkplaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/workplaces")
public class ApiWorkplaceController {

    private final WorkplaceService workplaceService;

    @GetMapping
    public List<MapWorkplaceDto> workplacesForMap() {
        return workplaceService.getMapWorkplaces();
    }
}
