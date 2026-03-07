package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class StockChangeMark {
    private LocalDate tradeDate;
    private String stockCode;
    private String stockName;
    private String changeType;
    private BigDecimal totalPrice;
    private BigDecimal price;
    private String changerName;
    private String changerPosition;
}
