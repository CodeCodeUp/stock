package com.example.brich.service;

import com.example.brich.mapper.DailyStockChangeMapper;
import com.example.brich.model.AggregatedChange;
import com.example.brich.model.AggregatedChangeDto;
import com.example.brich.model.DailyStockChange;
import com.example.brich.model.PricePointDto;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class StockService {
    @Autowired
    private DailyStockChangeMapper mapper;

    public List<AggregatedChange> getAggregatedChanges(LocalDate start, LocalDate end, String changeType, String changeSort, BigDecimal totalPrice) {
        List<AggregatedChangeDto> rawList = mapper.findAggregatedChangesByDay(start, end, changeType, totalPrice);
        // 1. 按 (tradeDate, stockCode, stockName) 分组
        Map<List<Object>, List<AggregatedChangeDto>> grouped = rawList.stream()
                .collect(Collectors.groupingBy(item ->
                        Arrays.asList(item.getTradeDate(), item.getStockCode(), item.getStockName())
                ));

        // 2. 对每组做汇总
        List<AggregatedChange> result = new ArrayList<>();
        for (Map.Entry<List<Object>, List<AggregatedChangeDto>> entry : grouped.entrySet()) {
            List<Object> key = entry.getKey();
            LocalDate date = (LocalDate) key.get(0);
            String code   = (String)   key.get(1);
            String name   = (String)   key.get(2);

            BigDecimal incSum = BigDecimal.ZERO;
            BigDecimal decSum = BigDecimal.ZERO;
            Set<String> names = new LinkedHashSet<>();
            Set<String> poses = new LinkedHashSet<>();

            for (AggregatedChangeDto rec : entry.getValue()) {
                // 累加增持/减持
                if ("增持".equals(rec.getChangeType())) {
                    incSum = incSum.add(rec.getTotalPrice());
                } else if ("减持".equals(rec.getChangeType())) {
                    decSum = decSum.add(rec.getTotalPrice());
                }
                // 收集不重复的姓名和职位
                names.add(rec.getChangerName());
                poses.add(rec.getChangerPosition());
            }

            AggregatedChange dto = new AggregatedChange();
            dto.setTradeDate(date);
            dto.setStockCode(code);
            dto.setStockName(name);
            dto.setTotalIncrease(incSum);
            dto.setTotalDecrease(decSum);
            // 用逗号拼接
            dto.setChangerName(String.join(",", names));
            dto.setChangerPosition(String.join(",", poses));

            result.add(dto);
        }
        // 将相同code的进行合并，日期选最早一天，totalIncrease和totalDecrease各自相加
        Map<String, List<AggregatedChange>> codeGrouped = result.stream()
                .collect(Collectors.groupingBy(AggregatedChange::getStockCode));

        List<AggregatedChange> mergedResult = new ArrayList<>();
        for (Map.Entry<String, List<AggregatedChange>> entry : codeGrouped.entrySet()) {
            List<AggregatedChange> sameCodeRecords = entry.getValue();

            // 只有一条记录不需要合并
            if (sameCodeRecords.size() == 1) {
                mergedResult.add(sameCodeRecords.get(0));
                continue;
            }

            // 合并同一股票代码的记录
            AggregatedChange merged = new AggregatedChange();
            String stockCode = entry.getKey();
            merged.setStockCode(stockCode);
            merged.setStockName(sameCodeRecords.get(0).getStockName());

            // 找最早的交易日期
            LocalDate earliestDate = sameCodeRecords.stream()
                    .map(AggregatedChange::getTradeDate)
                    .min(LocalDate::compareTo)
                    .orElse(null);
            merged.setTradeDate(earliestDate);

            // 汇总增持和减持金额
            BigDecimal totalIncrease = sameCodeRecords.stream()
                    .map(AggregatedChange::getTotalIncrease)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            BigDecimal totalDecrease = sameCodeRecords.stream()
                    .map(AggregatedChange::getTotalDecrease)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            merged.setTotalIncrease(totalIncrease);
            merged.setTotalDecrease(totalDecrease);

            // 合并人员名称和职位
            Set<String> names = new LinkedHashSet<>();
            Set<String> positions = new LinkedHashSet<>();
            Set<String> types = new LinkedHashSet<>();

            for (AggregatedChange record : sameCodeRecords) {
                if (record.getChangerName() != null) {
                    names.addAll(Arrays.asList(record.getChangerName().split(",")));
                }
                if (record.getChangerPosition() != null) {
                    positions.addAll(Arrays.asList(record.getChangerPosition().split(",")));
                }

            }
            merged.setChangerName(String.join(",", names));
            merged.setChangerPosition(String.join(",", positions));

            mergedResult.add(merged);
        }

        // 3. 根据排序参数决定排序方式
        if (changeSort != null && !changeSort.isEmpty()) {

            Comparator<AggregatedChange> comparator = Comparator.comparing(
                item -> item.getTotalIncrease().add(item.getTotalDecrease())
            );

            if ("desc".equalsIgnoreCase(changeSort)) {
                // 降序排序
                mergedResult.sort(comparator.reversed());
            } else if ("asc".equalsIgnoreCase(changeSort)) {
                // 升序排序
                mergedResult.sort(comparator);
            }
        } else {
            // 默认按日期倒序排序
            mergedResult.sort(Comparator.comparing(AggregatedChange::getTradeDate).reversed());
        }

        return mergedResult;
    }

    public List<PricePointDto> getPricePoints(String code) {
        return mapper.findPricePoints(code);
    }

    public List<AggregatedChangeDto> getMarks(String code) {
        return mapper.findMarks(code);
    }
}
