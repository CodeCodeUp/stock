package com.example.brich.model;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class PricePointDto {
    private LocalDateTime trackTime;
    private BigDecimal currentPrice;
}
