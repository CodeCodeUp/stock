package com.example.brich.service;

import com.example.brich.mapper.BacktestMapper;
import com.example.brich.model.BacktestEventDetail;
import com.example.brich.model.BacktestEventItem;
import com.example.brich.model.BacktestMetricItem;
import com.example.brich.model.BacktestOverview;
import com.example.brich.model.PageResult;
import com.example.brich.model.BacktestPriceBar;
import com.example.brich.model.BacktestRebuildResponse;
import com.example.brich.model.StockBacktestSummary;
import com.example.brich.model.StockChangeMark;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.util.UriComponentsBuilder;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import static org.springframework.http.HttpStatus.BAD_GATEWAY;

@Service
@RequiredArgsConstructor
public class BacktestService {
    private static final int MAX_QUERY_DAYS = 3660;

    private final BacktestMapper mapper;
    private final RestTemplate restTemplate;

    @org.springframework.beans.factory.annotation.Value("${data-api.url:http://localhost:5000}")
    private String dataApiUrl;

    public BacktestOverview getOverview(
            LocalDate start,
            LocalDate end,
            String keyword,
            BigDecimal minIncreaseAmount,
            Integer minSignalScore,
            Integer minBacktestScore,
            Boolean hasSameDayDecrease
    ) {
        validateOptionalDateRange(start, end, MAX_QUERY_DAYS, "回测日期范围不能超过 3660 天");
        BacktestOverview overview = mapper.getBacktestOverview(
                start,
                end,
                keyword,
                minIncreaseAmount,
                minSignalScore,
                minBacktestScore,
                hasSameDayDecrease
        );
        return overview == null ? new BacktestOverview() : overview;
    }

    public PageResult<BacktestEventItem> getEvents(
            LocalDate start,
            LocalDate end,
            String keyword,
            BigDecimal minIncreaseAmount,
            Integer minSignalScore,
            Integer minBacktestScore,
            Boolean hasSameDayDecrease,
            String sortBy,
            String sortOrder,
            int page,
            int pageSize
    ) {
        validateOptionalDateRange(start, end, MAX_QUERY_DAYS, "回测日期范围不能超过 3660 天");
        int offset = (page - 1) * pageSize;
        long total = mapper.countBacktestEvents(
                start,
                end,
                keyword,
                minIncreaseAmount,
                minSignalScore,
                minBacktestScore,
                hasSameDayDecrease
        );
        List<BacktestEventItem> items = total == 0
                ? List.of()
                : mapper.findBacktestEvents(
                start,
                end,
                keyword,
                minIncreaseAmount,
                minSignalScore,
                minBacktestScore,
                hasSameDayDecrease,
                sortBy,
                sortOrder,
                offset,
                pageSize
        );
        return PageResult.of(items, total, page, pageSize);
    }

    public StockBacktestSummary getStockSummary(String code) {
        StockBacktestSummary summary = mapper.findStockBacktestSummary(code);
        if (summary == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "未找到该股票的回测画像");
        }
        return summary;
    }

    public BacktestEventDetail getEventDetail(Long eventId) {
        BacktestEventItem event = mapper.findBacktestEventById(eventId);
        if (event == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "未找到该回测事件");
        }

        List<BacktestMetricItem> metrics = mapper.findBacktestMetricsByEventId(eventId);
        LocalDate signalDate = event.getSignalDate();
        LocalDate startDate = signalDate == null ? null : signalDate.minusDays(60);
        LocalDate endDate = signalDate == null ? null : signalDate.plusDays(180);
        List<BacktestPriceBar> priceBars = mapper.findBacktestPriceBars(event.getStockCode(), startDate, endDate);
        List<StockChangeMark> marks = mapper.findBacktestMarks(event.getStockCode(), startDate, endDate);

        BacktestEventDetail detail = new BacktestEventDetail();
        detail.setEvent(event);
        detail.setStockSummary(getStockSummary(event.getStockCode()));
        detail.setMetrics(metrics);
        detail.setPriceBars(priceBars);
        detail.setMarks(marks);
        return detail;
    }

    public BacktestRebuildResponse triggerRebuild(String mode) {
        String normalizedMode = (mode == null || mode.isBlank()) ? "incremental" : mode.trim().toLowerCase();
        if (!"incremental".equals(normalizedMode) && !"full".equals(normalizedMode)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "mode 仅支持 incremental 或 full");
        }

        String rebuildUrl = UriComponentsBuilder
                .fromHttpUrl(buildDataApiBaseUrl() + "/backtest/rebuild")
                .queryParam("mode", normalizedMode)
                .toUriString();

        try {
            Map<String, Object> response = restTemplate.postForObject(rebuildUrl, null, Map.class);
            Object responseData = response == null ? null : response.get("data");

            BacktestRebuildResponse result = new BacktestRebuildResponse();
            result.setMode(normalizedMode);
            result.setStatus("accepted");
            result.setMessage("回测任务已提交");

            if (responseData instanceof Map<?, ?> dataMap) {
                Object status = dataMap.get("status");
                Object message = dataMap.get("message");
                if (status instanceof String statusText) {
                    result.setStatus(statusText);
                }
                if (message instanceof String messageText) {
                    result.setMessage(messageText);
                }
            }

            return result;
        } catch (RestClientException exception) {
            throw new ResponseStatusException(BAD_GATEWAY, "下游回测任务服务请求失败", exception);
        }
    }

    private void validateOptionalDateRange(LocalDate start, LocalDate end, int maxDays, String maxDaysMessage) {
        if (start == null && end == null) {
            return;
        }
        if (start == null || end == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "开始日期和结束日期必须同时提供");
        }
        if (start.isAfter(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "开始日期不能晚于结束日期");
        }
        if (start.plusDays(maxDays).isBefore(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, maxDaysMessage);
        }
    }

    private String buildDataApiBaseUrl() {
        return dataApiUrl.endsWith("/") ? dataApiUrl.substring(0, dataApiUrl.length() - 1) : dataApiUrl;
    }
}
