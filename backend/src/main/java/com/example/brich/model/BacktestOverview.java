package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class BacktestOverview {
    private Long totalEvents = 0L;
    private Long totalStocks = 0L;
    private BigDecimal avgSignalScore = BigDecimal.ZERO;
    private BigDecimal avgBacktestScore = BigDecimal.ZERO;
    private BigDecimal winRate20d = BigDecimal.ZERO;
    private BigDecimal avgReturn20d = BigDecimal.ZERO;
    private BigDecimal hit10PctRate60d = BigDecimal.ZERO;
    private LocalDate latestSignalDate;
}
