package com.example.brich.controller;

import com.example.brich.model.AggregatedChangeDto;
import com.example.brich.model.PricePointDto;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
public class ChartResponse {
    private List<PricePointDto> priceData;
    private List<AggregatedChangeDto> marks;

    public ChartResponse(List<PricePointDto> priceData, List<AggregatedChangeDto> marks) {
        this.priceData = priceData;
        this.marks = marks;
    }
}