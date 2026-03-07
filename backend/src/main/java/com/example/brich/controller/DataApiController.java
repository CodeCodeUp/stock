package com.example.brich.controller;

import com.example.brich.model.ApiResponse;
import com.example.brich.model.PricePointDto;
import com.example.brich.model.StockChangeMark;
import jakarta.validation.constraints.Pattern;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.util.UriComponentsBuilder;

import java.math.BigDecimal;
import java.net.URLDecoder;
import java.text.SimpleDateFormat;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

import static org.springframework.http.HttpStatus.BAD_GATEWAY;
import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Slf4j
@Validated
@RestController
@RequestMapping("/data/api")
public class DataApiController {

    private static final String HOLD_PATH = "/stock_hold_management";
    private static final String HIST_PATH = "/stock_hist_day";
    private static final Set<String> SUPPORTED_PERIODS = Set.of("daily", "weekly", "monthly");

    @Value("${data-api.url:http://localhost:5000}")
    private String dataApiUrl;

    private final RestTemplate restTemplate;
    private final Executor dataApiExecutor;

    public DataApiController(RestTemplate restTemplate, @Qualifier("dataApiExecutor") Executor dataApiExecutor) {
        this.restTemplate = restTemplate;
        this.dataApiExecutor = dataApiExecutor;
    }

    @GetMapping("/detail/chart")
    public ApiResponse<ChartResponse> chart(
            @RequestParam("code")
            @Pattern(regexp = "^[0-9A-Za-z]{6,10}$", message = "股票代码格式不正确")
            String code,
            @RequestParam("name") String name,
            @RequestParam(value = "period", required = false, defaultValue = "daily") String period
    ) {
        String normalizedPeriod = normalizePeriod(period);
        List<String> names = parseNames(name);

        try {
            List<Map<String, Object>> allHoldData = fetchAllHoldData(code, names);
            if (allHoldData.isEmpty()) {
                return ApiResponse.success(new ChartResponse(Collections.emptyList(), Collections.emptyList()));
            }

            String begin = getBeginDateFromHoldData(allHoldData);
            List<Map<String, Object>> histData = fetchHistoryData(code, begin, normalizedPeriod);
            List<PricePointDto> priceData = convertToPriceData(histData);
            List<StockChangeMark> marks = convertToMarks(allHoldData);

            return ApiResponse.success(new ChartResponse(priceData, marks));
        } catch (CompletionException exception) {
            throw unwrapCompletionException(exception);
        }
    }

    private String normalizePeriod(String period) {
        String normalized = period == null ? "daily" : period.trim().toLowerCase(Locale.ROOT);
        if (!SUPPORTED_PERIODS.contains(normalized)) {
            throw new ResponseStatusException(BAD_REQUEST, "period 只支持 daily、weekly、monthly");
        }
        return normalized;
    }

    private List<String> parseNames(String name) {
        List<String> names = java.util.Arrays.stream(name.split(","))
                .map(value -> URLDecoder.decode(value, StandardCharsets.UTF_8))
                .map(String::trim)
                .filter(value -> !value.isEmpty())
                .distinct()
                .toList();

        if (names.isEmpty()) {
            throw new ResponseStatusException(BAD_REQUEST, "缺少有效的变动人姓名");
        }
        return names;
    }

    private List<Map<String, Object>> fetchAllHoldData(String code, List<String> names) {
        List<CompletableFuture<List<Map<String, Object>>>> futures = names.stream()
                .map(singleName -> CompletableFuture.supplyAsync(() -> fetchHoldData(code, singleName), dataApiExecutor))
                .toList();

        List<Map<String, Object>> merged = new ArrayList<>();
        for (CompletableFuture<List<Map<String, Object>>> future : futures) {
            merged.addAll(future.join());
        }
        return merged;
    }

    private List<Map<String, Object>> fetchHoldData(String code, String singleName) {
        String holdUrl = UriComponentsBuilder
                .fromHttpUrl(buildDataApiBaseUrl() + HOLD_PATH)
                .queryParam("name", singleName)
                .queryParam("code", code)
                .toUriString();

        try {
            List<Map<String, Object>> holdData = restTemplate.getForObject(holdUrl, List.class);
            return holdData == null ? List.of() : holdData;
        } catch (RestClientException exception) {
            log.warn("请求持股明细失败 code={} name={}", code, singleName, exception);
            throw new ResponseStatusException(BAD_GATEWAY, "下游增减持数据服务请求失败");
        }
    }

    private List<Map<String, Object>> fetchHistoryData(String code, String begin, String period) {
        String histUrl = UriComponentsBuilder
                .fromHttpUrl(buildDataApiBaseUrl() + HIST_PATH)
                .queryParam("begin", begin)
                .queryParam("code", code)
                .queryParam("period", period)
                .toUriString();

        try {
            List<Map<String, Object>> histData = restTemplate.getForObject(histUrl, List.class);
            return histData == null ? List.of() : histData;
        } catch (RestClientException exception) {
            log.warn("请求历史价格失败 code={} begin={} period={}", code, begin, period, exception);
            throw new ResponseStatusException(BAD_GATEWAY, "下游历史价格服务请求失败");
        }
    }

    private String getBeginDateFromHoldData(List<Map<String, Object>> holdData) {
        LocalDateTime earliestDate = holdData.stream()
                .map(item -> parseDateTime((String) item.get("日期")))
                .filter(Objects::nonNull)
                .min(LocalDateTime::compareTo)
                .orElseThrow(() -> new ResponseStatusException(BAD_GATEWAY, "下游增减持数据缺少有效日期"));

        return earliestDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
    }

    private List<PricePointDto> convertToPriceData(List<Map<String, Object>> histData) {
        if (histData == null) {
            return Collections.emptyList();
        }

        return histData.stream()
                .map(item -> {
                    LocalDateTime trackTime = parseDateTime((String) item.get("日期"));
                    BigDecimal currentPrice = toBigDecimal(item.get("收盘"));
                    if (trackTime == null || currentPrice == null) {
                        return null;
                    }

                    PricePointDto dto = new PricePointDto();
                    dto.setTrackTime(trackTime);
                    dto.setCurrentPrice(currentPrice);
                    return dto;
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    private List<StockChangeMark> convertToMarks(List<Map<String, Object>> holdData) {
        if (holdData == null) {
            return Collections.emptyList();
        }

        return holdData.stream()
                .map(item -> {
                    LocalDateTime parsedDate = parseDateTime((String) item.get("日期"));
                    if (parsedDate == null) {
                        return null;
                    }

                    StockChangeMark dto = new StockChangeMark();
                    dto.setStockCode((String) item.get("代码"));
                    dto.setStockName((String) item.get("名称"));
                    dto.setTradeDate(parsedDate.toLocalDate());
                    dto.setChangeType(resolveChangeType(item.get("变动股数")));
                    dto.setTotalPrice(toAbsoluteBigDecimal(item.get("变动金额")));
                    dto.setChangerName((String) item.get("变动人"));
                    dto.setChangerPosition((String) item.get("职务"));
                    dto.setPrice(toBigDecimal(item.get("成交均价")));
                    return dto;
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    private String resolveChangeType(Object shares) {
        BigDecimal shareValue = toBigDecimal(shares);
        if (shareValue == null) {
            return null;
        }
        return shareValue.signum() < 0 ? "减持" : "增持";
    }

    private BigDecimal toAbsoluteBigDecimal(Object value) {
        BigDecimal result = toBigDecimal(value);
        return result == null ? null : result.abs();
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof BigDecimal bigDecimal) {
            return bigDecimal;
        }
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue());
        }

        String text = String.valueOf(value).trim();
        if (text.isEmpty() || "null".equalsIgnoreCase(text) || "nan".equalsIgnoreCase(text) || "--".equals(text)) {
            return null;
        }

        try {
            return new BigDecimal(text);
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private LocalDateTime parseDateTime(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }

        try {
            SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss zzz", Locale.US);
            Date date = sdf.parse(dateStr);
            return date == null ? null : date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
        } catch (Exception exception) {
            return null;
        }
    }

    private ResponseStatusException unwrapCompletionException(CompletionException exception) {
        Throwable cause = exception.getCause();
        if (cause instanceof ResponseStatusException responseStatusException) {
            return responseStatusException;
        }
        return new ResponseStatusException(BAD_GATEWAY, "下游数据服务请求失败", exception);
    }

    private String buildDataApiBaseUrl() {
        return dataApiUrl.endsWith("/") ? dataApiUrl.substring(0, dataApiUrl.length() - 1) : dataApiUrl;
    }
}
