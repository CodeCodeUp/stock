package com.example.brich.mapper;

import com.example.brich.model.BacktestEventItem;
import com.example.brich.model.BacktestMetricItem;
import com.example.brich.model.BacktestOverview;
import com.example.brich.model.BacktestPriceBar;
import com.example.brich.model.StockBacktestSummary;
import com.example.brich.model.StockChangeMark;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Mapper
public interface BacktestMapper {
    BacktestOverview getBacktestOverview(
            @Param("start") LocalDate start,
            @Param("end") LocalDate end,
            @Param("keyword") String keyword,
            @Param("minIncreaseAmount") BigDecimal minIncreaseAmount,
            @Param("minSignalScore") Integer minSignalScore,
            @Param("minBacktestScore") Integer minBacktestScore,
            @Param("hasSameDayDecrease") Boolean hasSameDayDecrease
    );

    long countBacktestEvents(
            @Param("start") LocalDate start,
            @Param("end") LocalDate end,
            @Param("keyword") String keyword,
            @Param("minIncreaseAmount") BigDecimal minIncreaseAmount,
            @Param("minSignalScore") Integer minSignalScore,
            @Param("minBacktestScore") Integer minBacktestScore,
            @Param("hasSameDayDecrease") Boolean hasSameDayDecrease
    );

    List<BacktestEventItem> findBacktestEvents(
            @Param("start") LocalDate start,
            @Param("end") LocalDate end,
            @Param("keyword") String keyword,
            @Param("minIncreaseAmount") BigDecimal minIncreaseAmount,
            @Param("minSignalScore") Integer minSignalScore,
            @Param("minBacktestScore") Integer minBacktestScore,
            @Param("hasSameDayDecrease") Boolean hasSameDayDecrease,
            @Param("sortBy") String sortBy,
            @Param("sortOrder") String sortOrder,
            @Param("offset") int offset,
            @Param("pageSize") int pageSize
    );

    BacktestEventItem findBacktestEventById(@Param("eventId") Long eventId);

    List<BacktestMetricItem> findBacktestMetricsByEventId(@Param("eventId") Long eventId);

    List<BacktestPriceBar> findBacktestPriceBars(
            @Param("stockCode") String stockCode,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate
    );

    List<StockChangeMark> findBacktestMarks(
            @Param("stockCode") String stockCode,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate
    );

    StockBacktestSummary findStockBacktestSummary(@Param("code") String code);
}
