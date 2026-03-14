package com.example.brich.model;

import lombok.Data;

import java.util.List;

@Data
public class BacktestEventDetail {
    private BacktestEventItem event;
    private StockBacktestSummary stockSummary;
    private List<BacktestMetricItem> metrics;
    private List<BacktestPriceBar> priceBars;
    private List<StockChangeMark> marks;
}
