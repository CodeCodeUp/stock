package com.example.brich.service;

import com.example.brich.controller.ChartResponse;
import com.example.brich.mapper.DailyStockChangeMapper;
import com.example.brich.model.PageResult;
import com.example.brich.model.PricePointDto;
import com.example.brich.model.StockChangeMark;
import com.example.brich.model.StockChangeSummary;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class StockService {
    private static final int MAX_QUERY_DAYS = 366;

    private final DailyStockChangeMapper mapper;

    public PageResult<StockChangeSummary> getStockChangeSummaries(
            LocalDate start,
            LocalDate end,
            String changeType,
            String changeSort,
            BigDecimal totalPrice,
            int page,
            int pageSize
    ) {
        validateDateRange(start, end, MAX_QUERY_DAYS, "列表查询日期范围不能超过 366 天");

        int offset = (page - 1) * pageSize;
        long total = mapper.countStockChangeSummaries(start, end, changeType, totalPrice);
        List<StockChangeSummary> items = total == 0
                ? List.of()
                : mapper.findStockChangeSummaries(start, end, changeType, totalPrice, changeSort, offset, pageSize);

        return PageResult.of(items, total, page, pageSize);
    }

    public ChartResponse getChart(String code, LocalDate start, LocalDate end) {
        if (code == null || code.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "股票代码不能为空");
        }

        if (start != null && end != null) {
            validateDateRange(start, end, MAX_QUERY_DAYS, "图表查询日期范围不能超过 366 天");
        }

        LocalDateTime startTime = start == null ? null : start.atStartOfDay();
        LocalDateTime endTime = end == null ? null : end.plusDays(1).atStartOfDay();
        List<PricePointDto> prices = mapper.findPricePoints(code, startTime, endTime);
        List<StockChangeMark> marks = mapper.findMarks(code, start, end);
        return new ChartResponse(prices, marks);
    }

    private void validateDateRange(LocalDate start, LocalDate end, int maxDays, String maxDaysMessage) {
        if (start == null || end == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "开始日期和结束日期不能为空");
        }
        if (start.isAfter(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "开始日期不能晚于结束日期");
        }
        if (start.plusDays(maxDays).isBefore(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, maxDaysMessage);
        }
    }
}
