package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class BacktestEventItem {
    private Long eventId;
    private String stockCode;
    private String stockName;
    private LocalDate signalDate;
    private String eventScope;
    private Integer increaseCount;
    private BigDecimal increaseAmount;
    private BigDecimal increaseRatioSum;
    private BigDecimal increaseRatioMax;
    private Integer changerCount;
    private String changerNames;
    private String positionTags;
    private Boolean hasSameDayDecrease;
    private BigDecimal sameDayDecreaseAmount;
    private Integer consecutiveIncreaseDays;
    private Integer signalScore;
    private Integer backtestScore;
    private BigDecimal return5d;
    private BigDecimal return10d;
    private BigDecimal return20d;
    private BigDecimal return60d;
}
