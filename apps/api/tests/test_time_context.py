from datetime import datetime, timezone
import pytest
from app.services.time_context import local_now, meal_period
@pytest.mark.parametrize(('hour','minute','expected'),[(4,59,'late-night'),(5,0,'breakfast'),(10,29,'breakfast'),(10,30,'lunch'),(14,29,'lunch'),(14,30,'snacks'),(17,29,'snacks'),(17,30,'dinner'),(21,59,'dinner'),(22,0,'late-night')])
def test_meal_boundaries(hour,minute,expected): assert meal_period(datetime(2026,1,1,hour,minute))==expected
def test_local_now_chicago():
 value=local_now('America/Chicago',datetime(2026,1,1,18,0,tzinfo=timezone.utc));assert value.tzinfo is not None;assert str(value.tzinfo)=='America/Chicago';assert meal_period(value)=='lunch'
