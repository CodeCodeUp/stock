package com.example.brich.model;


import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class AggregatedChange {
    private LocalDate tradeDate;
    private String stockCode;
    private String stockName;
    private BigDecimal totalIncrease;
    private BigDecimal totalDecrease;
    private String changerName;
    private String changerPosition;
}
