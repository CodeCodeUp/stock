package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class StockChangeSummary {
    private String stockCode;
    private String stockName;
    private LocalDate firstTradeDate;
    private LocalDate latestTradeDate;
    private Integer changeCount;
    private BigDecimal totalIncrease;
    private BigDecimal totalDecrease;
    private BigDecimal totalAmount;
    private String changerName;
    private String changerPosition;
}
