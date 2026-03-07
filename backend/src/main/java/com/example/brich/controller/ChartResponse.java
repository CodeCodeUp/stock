package com.example.brich.controller;

import com.example.brich.model.PricePointDto;
import com.example.brich.model.StockChangeMark;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
public class ChartResponse {
    private List<PricePointDto> priceData;
    private List<StockChangeMark> marks;

    public ChartResponse(List<PricePointDto> priceData, List<StockChangeMark> marks) {
        this.priceData = priceData;
        this.marks = marks;
    }
}
