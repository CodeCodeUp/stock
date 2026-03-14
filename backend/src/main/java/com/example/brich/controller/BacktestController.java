package com.example.brich.controller;

import com.example.brich.model.ApiResponse;
import com.example.brich.model.BacktestEventItem;
import com.example.brich.model.BacktestEventDetail;
import com.example.brich.model.BacktestOverview;
import com.example.brich.model.BacktestRebuildResponse;
import com.example.brich.model.PageResult;
import com.example.brich.model.StockBacktestSummary;
import com.example.brich.service.BacktestService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.time.LocalDate;

@Validated
@RestController
@RequestMapping("/api/backtest")
@RequiredArgsConstructor
public class BacktestController {

    private final BacktestService service;

    @GetMapping("/overview")
    public ApiResponse<BacktestOverview> overview(
            @RequestParam(value = "start", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam(value = "end", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "minIncreaseAmount", required = false) BigDecimal minIncreaseAmount,
            @RequestParam(value = "minSignalScore", required = false) @Min(0) @Max(100) Integer minSignalScore,
            @RequestParam(value = "minBacktestScore", required = false) @Min(0) @Max(100) Integer minBacktestScore,
            @RequestParam(value = "hasSameDayDecrease", required = false) Boolean hasSameDayDecrease
    ) {
        return ApiResponse.success(
                service.getOverview(
                        start,
                        end,
                        keyword,
                        minIncreaseAmount,
                        minSignalScore,
                        minBacktestScore,
                        hasSameDayDecrease
                )
        );
    }

    @GetMapping("/events")
    public ApiResponse<PageResult<BacktestEventItem>> events(
            @RequestParam(value = "start", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam(value = "end", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "minIncreaseAmount", required = false) BigDecimal minIncreaseAmount,
            @RequestParam(value = "minSignalScore", required = false) @Min(0) @Max(100) Integer minSignalScore,
            @RequestParam(value = "minBacktestScore", required = false) @Min(0) @Max(100) Integer minBacktestScore,
            @RequestParam(value = "hasSameDayDecrease", required = false) Boolean hasSameDayDecrease,
            @RequestParam(value = "sortBy", required = false)
            @Pattern(
                    regexp = "^(signalDate|increaseAmount|signalScore|backtestScore|return20d|return60d)?$",
                    message = "sortBy 仅支持 signalDate、increaseAmount、signalScore、backtestScore、return20d、return60d"
            )
            String sortBy,
            @RequestParam(value = "sortOrder", required = false)
            @Pattern(regexp = "^(asc|desc)?$", message = "sortOrder 仅支持 asc 或 desc")
            String sortOrder,
            @RequestParam(value = "page", defaultValue = "1") @Min(1) int page,
            @RequestParam(value = "pageSize", defaultValue = "20") @Min(1) @Max(100) int pageSize
    ) {
        return ApiResponse.success(
                service.getEvents(
                        start,
                        end,
                        keyword,
                        minIncreaseAmount,
                        minSignalScore,
                        minBacktestScore,
                        hasSameDayDecrease,
                        sortBy,
                        sortOrder,
                        page,
                        pageSize
                )
        );
    }

    @GetMapping("/stocks/{code}/summary")
    public ApiResponse<StockBacktestSummary> stockSummary(
            @PathVariable
            @Pattern(regexp = "^[0-9A-Za-z]{6,10}$", message = "股票代码格式不正确")
            String code
    ) {
        return ApiResponse.success(service.getStockSummary(code));
    }

    @GetMapping("/events/{eventId}")
    public ApiResponse<BacktestEventDetail> eventDetail(
            @PathVariable("eventId") @Min(1) Long eventId
    ) {
        return ApiResponse.success(service.getEventDetail(eventId));
    }

    @PostMapping("/rebuild")
    public ApiResponse<BacktestRebuildResponse> rebuild(
            @RequestParam(value = "mode", required = false, defaultValue = "incremental")
            @Pattern(regexp = "^(incremental|full)$", message = "mode 仅支持 incremental 或 full")
            String mode
    ) {
        return ApiResponse.success(service.triggerRebuild(mode));
    }
}
