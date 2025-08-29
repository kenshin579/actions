#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
this_week_range_kst 함수의 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from main import this_week_range_kst

# KST 타임존
KST = ZoneInfo("Asia/Seoul")


class TestThisWeekRangeKST:
    """this_week_range_kst 함수 테스트 클래스"""

    @pytest.mark.parametrize("test_date,expected_start,expected_end", [
        # 2024년 3월 기준 테스트 데이터 (토요일: 2024-03-02, 일요일: 2024-03-03, 월요일: 2024-03-04 등)

        # 월요일 (weekday=0) - 전주 토요일 ~ 이번주 금요일
        ("2024-03-04", "2024-03-02 00:00:00", "2024-03-08 23:59:59"),  # 3월 4일(월) -> 3월 2일(토) ~ 3월 8일(금)

        # 화요일 (weekday=1) - 전주 토요일 ~ 이번주 금요일
        ("2024-03-05", "2024-03-02 00:00:00", "2024-03-08 23:59:59"),  # 3월 5일(화) -> 3월 2일(토) ~ 3월 8일(금)

        # 수요일 (weekday=2) - 전주 토요일 ~ 이번주 금요일
        ("2024-03-06", "2024-03-02 00:00:00", "2024-03-08 23:59:59"),  # 3월 6일(수) -> 3월 2일(토) ~ 3월 8일(금)

        # 목요일 (weekday=3) - 전주 토요일 ~ 이번주 금요일
        ("2024-03-07", "2024-03-02 00:00:00", "2024-03-08 23:59:59"),  # 3월 7일(목) -> 3월 2일(토) ~ 3월 8일(금)

        # 금요일 (weekday=4) - 전주 토요일 ~ 이번주 금요일
        ("2024-03-08", "2024-03-02 00:00:00", "2024-03-08 23:59:59"),  # 3월 8일(금) -> 3월 2일(토) ~ 3월 8일(금)

        # 토요일 (weekday=5) - 이번주 토요일 ~ 다음주 금요일
        ("2024-03-09", "2024-03-09 00:00:00", "2024-03-15 23:59:59"),  # 3월 9일(토) -> 3월 9일(토) ~ 3월 15일(금)

        # 일요일 (weekday=6) - 이번주 토요일 ~ 다음주 금요일
        ("2024-03-10", "2024-03-09 00:00:00", "2024-03-15 23:59:59"),  # 3월 10일(일) -> 3월 9일(토) ~ 3월 15일(금)
    ])
    def test_weekday_ranges(self, test_date, expected_start, expected_end):
        """각 요일별 주간 범위 테스트"""
        test_datetime = datetime.fromisoformat(test_date).replace(tzinfo=KST)
        start, end = this_week_range_kst(test_datetime)

        expected_start_dt = datetime.fromisoformat(expected_start).replace(tzinfo=KST)
        expected_end_dt = datetime.fromisoformat(expected_end).replace(tzinfo=KST)

        assert start == expected_start_dt, f"Start mismatch: {start} != {expected_start_dt}"
        assert end == expected_end_dt, f"End mismatch: {end} != {expected_end_dt}"

    def test_current_datetime(self):
        """현재 시간으로 함수 호출 시 정상 작동하는지 테스트"""
        start, end = this_week_range_kst()

        # 결과가 datetime 객체인지 확인
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)

        # 시작일이 종료일보다 이전인지 확인
        assert start < end

        # 시작일이 00:00:00인지 확인
        assert start.hour == 0 and start.minute == 0 and start.second == 0

        # 종료일이 23:59:59인지 확인
        assert end.hour == 23 and end.minute == 59 and end.second == 59

        # KST 타임존인지 확인
        assert start.tzinfo == KST
        assert end.tzinfo == KST

    def test_duration_always_7_days(self):
        """범위가 항상 7일인지 확인"""
        test_cases = [
            "2024-03-04",  # 월요일
            "2024-03-05",  # 화요일
            "2024-03-06",  # 수요일
            "2024-03-07",  # 목요일
            "2024-03-08",  # 금요일
            "2024-03-09",  # 토요일
            "2024-03-10",  # 일요일
        ]

        for date_str in test_cases:
            test_datetime = datetime.fromisoformat(date_str).replace(tzinfo=KST)
            start, end = this_week_range_kst(test_datetime)

            # 기간 계산 (종료일 - 시작일 + 1일 = 7일)
            duration_days = (end.date() - start.date()).days + 1
            assert duration_days == 7, f"Duration should be 7 days for {date_str}, got {duration_days}"

    def test_month_boundary(self):
        """월 경계 테스트"""
        # 1월 31일 금요일 -> 1월 25일 토요일 ~ 1월 31일 금요일
        test_datetime = datetime(2024, 1, 31, tzinfo=KST)  # 2024년 1월 31일은 수요일
        start, end = this_week_range_kst(test_datetime)

        assert start.month == 1 and start.day == 27  # 1월 27일 토요일
        assert end.month == 2 and end.day == 2      # 2월 2일 금요일

    def test_year_boundary(self):
        """연도 경계 테스트"""
        # 2023년 12월 31일 일요일 -> 2023년 12월 30일 토요일 ~ 2024년 1월 5일 금요일
        test_datetime = datetime(2023, 12, 31, tzinfo=KST)
        start, end = this_week_range_kst(test_datetime)

        assert start.year == 2023 and start.month == 12 and start.day == 30
        assert end.year == 2024 and end.month == 1 and end.day == 5

    def test_leap_year_february(self):
        """윤년 2월 테스트"""
        # 2024년 2월 29일 목요일 -> 2월 24일 토요일 ~ 3월 1일 금요일
        test_datetime = datetime(2024, 2, 29, tzinfo=KST)
        start, end = this_week_range_kst(test_datetime)

        assert start.year == 2024 and start.month == 2 and start.day == 24
        assert end.year == 2024 and end.month == 3 and end.day == 1

    def test_timezone_preservation(self):
        """타임존 보존 테스트"""
        test_datetime = datetime(2024, 3, 6, 15, 30, 45, tzinfo=KST)
        start, end = this_week_range_kst(test_datetime)

        assert start.tzinfo == KST
        assert end.tzinfo == KST
        assert start.tzinfo is not None
        assert end.tzinfo is not None

    def test_consistent_behavior(self):
        """동일한 입력에 대해 일관된 결과 반환 테스트"""
        test_datetime = datetime(2024, 3, 6, 15, 30, 45, tzinfo=KST)

        result1 = this_week_range_kst(test_datetime)
        result2 = this_week_range_kst(test_datetime)

        assert result1 == result2
        assert result1[0] == result2[0]
        assert result1[1] == result2[1]


if __name__ == "__main__":
    # 단독 실행 시 간단한 테스트 수행
    print("Running simple tests...")

    # 현재 시간으로 테스트
    start, end = this_week_range_kst()
    print(f"Current week range: {start} ~ {end}")

    # 특정 날짜로 테스트
    test_dates = [
        "2024-03-04",  # 월요일
        "2024-03-09",  # 토요일
        "2024-03-10",  # 일요일
    ]

    for date_str in test_dates:
        test_dt = datetime.fromisoformat(date_str).replace(tzinfo=KST)
        start, end = this_week_range_kst(test_dt)
        print(f"{date_str} ({test_dt.strftime('%a')}): {start.date()} ~ {end.date()}")

    print("Simple tests completed.")
