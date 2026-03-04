package com.example.brich.controller;

import com.example.brich.model.AggregatedChangeDto;
import com.example.brich.model.PricePointDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.*;
import java.util.stream.Collectors;
import java.text.SimpleDateFormat;

@RestController
@RequestMapping("/data/api")
public class DataApiController {

    private final static String URL = "116.205.244.106:5000";
    private final static String ALL = "/stock_hold_management";
    private final static String DETAIL = "/stock_hist_day";

    @Autowired
    private RestTemplate restTemplate;

    @GetMapping("/detail/chart")
    public ChartResponse chart(
            @RequestParam(value = "code") String code,
            @RequestParam(value = "name") String name,
            @RequestParam(value = "period", required = false) String period
    ) {
        try {
            // 拆分可能包含多个名称的参数
            String[] names = name.split(",");
            List<Map<String, Object>> allHoldData = new ArrayList<>();

            // 对每个名称调用API并合并结果
            for (String singleName : names) {
                String holdUrl = "http://" + URL + ALL + "?name=" + singleName.trim() + "&code=" + code;
                List<Map<String, Object>> currentHoldData = restTemplate.getForObject(holdUrl, List.class);
                if (currentHoldData != null && !currentHoldData.isEmpty()) {
                    allHoldData.addAll(currentHoldData);
                }
            }

            // 没有数据则返回空结果
            if (allHoldData.isEmpty()) {
                return new ChartResponse(Collections.emptyList(), Collections.emptyList());
            }

            // 从合并后的持股数据中获取最早的日期作为begin参数
            String begin = getBeginDateFromHoldData(allHoldData);

            // 调用第二个API获取股票历史价格
            String histUrl = "http://" + URL + DETAIL + "?begin=" + begin + "&code=" + code;
            List<Map<String, Object>> histData = restTemplate.getForObject(histUrl, List.class);

            // 转换数据
            List<PricePointDto> priceData = convertToPriceData(histData);
            List<AggregatedChangeDto> marks = convertToMarks(allHoldData);

            return new ChartResponse(priceData, marks);
        } catch (Exception e) {
            // 记录异常
            e.printStackTrace();
            return new ChartResponse(Collections.emptyList(), Collections.emptyList());
        }
    }

    /**
     * 从持股数据中获取最后一天的日期并转换为YYYYMMDD格式
     */
    private String getBeginDateFromHoldData(List<Map<String, Object>> holdData) {
        if (holdData == null || holdData.isEmpty()) {
            // 如果没有数据，返回当前日期
            return LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        }

        // 找到最新的一条记录（最后一天）
        LocalDateTime latestDate = holdData.stream()
                .map(item -> {
                    String dateStr = (String) item.get("日期");
                    return parseDateTime(dateStr);
                })
                .min(LocalDateTime::compareTo)
                .orElse(LocalDateTime.now());

        // 转换为YYYYMMDD格式
        return latestDate.format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
    }

    private List<PricePointDto> convertToPriceData(List<Map<String, Object>> histData) {
        if (histData == null) return Collections.emptyList();

        return histData.stream().map(item -> {
            PricePointDto dto = new PricePointDto();

            // 日期格式转换
            String dateStr = (String) item.get("日期");
            LocalDateTime trackTime = parseDateTime(dateStr);
            dto.setTrackTime(trackTime);

            // 收盘价作为当前价格
            Object closePrice = item.get("收盘");
            if (closePrice instanceof Number) {
                dto.setCurrentPrice(BigDecimal.valueOf(((Number) closePrice).doubleValue()));
            } else if (closePrice instanceof String) {
                dto.setCurrentPrice(new BigDecimal((String) closePrice));
            }

            return dto;
        }).collect(Collectors.toList());
    }

    private List<AggregatedChangeDto> convertToMarks(List<Map<String, Object>> holdData) {
        if (holdData == null) return Collections.emptyList();

        return holdData.stream().map(item -> {
            AggregatedChangeDto dto = new AggregatedChangeDto();

            // 基本信息
            dto.setStockCode((String) item.get("代码"));
            dto.setStockName((String) item.get("名称"));

            // 日期转换
            String dateStr = (String) item.get("日期");
            LocalDate tradeDate = parseDateTime(dateStr).toLocalDate();
            dto.setTradeDate(tradeDate);

            // 变动类型判断
            Object shares = item.get("变动股数");
            if (shares instanceof Number) {
                dto.setChangeType(((Number) shares).doubleValue() > 0 ? "增持" : "减持");
            }

            // 变动金额
            Object amount = item.get("变动金额");
            if (amount instanceof Number) {
                dto.setTotalPrice(BigDecimal.valueOf(((Number) amount).doubleValue()));
            }

            // 变动人和职务
            dto.setChangerName((String) item.get("变动人"));
            dto.setChangerPosition((String) item.get("职务"));

            dto.setPrice(String.valueOf(item.get("成交均价")));

            return dto;
        }).collect(Collectors.toList());
    }

    private LocalDateTime parseDateTime(String dateStr) {
        try {
            // 转换格式如："Mon, 19 May 2025 00:00:00 GMT"
            SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss zzz", Locale.US);
            Date date = sdf.parse(dateStr);
            return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
        } catch (Exception e) {
            return LocalDateTime.now(); // 解析失败时返回当前时间
        }
    }
}