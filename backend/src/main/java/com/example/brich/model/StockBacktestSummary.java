package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class StockBacktestSummary {
    private String stockCode;
    private String stockName;
    private Integer sampleEventCount;
    private BigDecimal winRate5d;
    private BigDecimal winRate10d;
    private BigDecimal winRate20d;
    private BigDecimal avgReturn5d;
    private BigDecimal avgReturn10d;
    private BigDecimal avgReturn20d;
    private BigDecimal medianReturn20d;
    private BigDecimal avgMaxDrawdown20d;
    private BigDecimal hit5pctRate20d;
    private BigDecimal hit10pctRate60d;
    private Integer historicalResponseScore;
    private Integer backtestScore;
    private LocalDate lastEventDate;
}
