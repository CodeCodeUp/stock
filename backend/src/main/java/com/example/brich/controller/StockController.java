package com.example.brich.controller;

import com.example.brich.model.ApiResponse;
import com.example.brich.model.PageResult;
import com.example.brich.model.StockChangeSummary;
import com.example.brich.service.StockService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.time.LocalDate;

@Validated
@RestController
@RequestMapping("/api/stocks")
@RequiredArgsConstructor
public class StockController {

    private final StockService service;

    @GetMapping("/changes")
    public ApiResponse<PageResult<StockChangeSummary>> changes(
            @RequestParam("start") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam("end") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @RequestParam(value = "changeType", required = false)
            @Pattern(regexp = "^(增持|减持)?$", message = "changeType 只支持 增持 或 减持")
            String changeType,
            @RequestParam(value = "changeSort", required = false)
            @Pattern(regexp = "^(asc|desc)?$", message = "changeSort 只支持 asc 或 desc")
            String changeSort,
            @RequestParam(value = "totalPrice", required = false) BigDecimal totalPrice,
            @RequestParam(value = "page", defaultValue = "1") @Min(value = 1, message = "page 必须大于等于 1") int page,
            @RequestParam(value = "pageSize", defaultValue = "20")
            @Min(value = 1, message = "pageSize 必须大于等于 1")
            @Max(value = 100, message = "pageSize 不能超过 100")
            int pageSize
    ) {
        return ApiResponse.success(service.getStockChangeSummaries(start, end, changeType, changeSort, totalPrice, page, pageSize));
    }

    @GetMapping("/{code}/chart")
    public ApiResponse<ChartResponse> chart(
            @PathVariable
            @Pattern(regexp = "^[0-9A-Za-z]{6,10}$", message = "股票代码格式不正确")
            String code,
            @RequestParam(value = "start", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam(value = "end", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end
    ) {
        return ApiResponse.success(service.getChart(code, start, end));
    }
}
