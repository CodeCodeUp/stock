package com.example.brich.model;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class DailyStockChange {
    private Integer recordId;
    private LocalDate tradeDate;
    private String stockCode;
    private String stockName;
    private String changeType;
    private String changerName;
    private BigDecimal changeShares;
    // ... 省略其他字段
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
