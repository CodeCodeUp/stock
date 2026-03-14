package com.example.brich.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class BacktestMetricItem {
    private Integer horizonDays;
    private LocalDate entryDate;
    private BigDecimal entryPrice;
    private String entryPriceType;
    private LocalDate exitDate;
    private BigDecimal exitPrice;
    private BigDecimal returnPct;
    private BigDecimal maxReturnPct;
    private BigDecimal maxDrawdownPct;
    private BigDecimal volatilityPct;
    private Boolean hit3pctFlag;
    private Boolean hit5pctFlag;
    private Boolean hit10pctFlag;
    private Boolean isPositiveFlag;
    private Integer barsCount;
}
