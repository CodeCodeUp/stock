package com.example.brich.mapper;


import com.example.brich.model.PricePointDto;
import com.example.brich.model.StockChangeMark;
import com.example.brich.model.StockChangeSummary;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface DailyStockChangeMapper {
    long countStockChangeSummaries(
            @Param("start") LocalDate start,
            @Param("end") LocalDate end,
            @Param("changeType") String changeType,
            @Param("totalPrice") BigDecimal totalPrice
    );

    List<StockChangeSummary> findStockChangeSummaries(
            @Param("start") LocalDate start,
            @Param("end") LocalDate end,
            @Param("changeType") String changeType,
            @Param("totalPrice") BigDecimal totalPrice,
            @Param("changeSort") String changeSort,
            @Param("offset") int offset,
            @Param("pageSize") int pageSize
    );

    List<PricePointDto> findPricePoints(
            @Param("code") String code,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime
    );

    List<StockChangeMark> findMarks(
            @Param("code") String code,
            @Param("start") LocalDate start,
            @Param("end") LocalDate end
    );
}
