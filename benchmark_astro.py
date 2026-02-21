import time
from models.astro_calc import get_moon_data_month, get_sun_events_month, get_moon_data, get_sun_events
from datetime import date

def benchmark():
    pref = "東京(東京都)"
    year = 2026
    month = 5
    day = 15
    date_str = f"{year}-{month:02d}-{day:02d}"

    print(f"--- Benchmarking Astro Calc for {pref}, {year}/{month} ---")

    # 1. Monthly Moon Data
    start = time.time()
    res1 = get_moon_data_month(pref, year, month)
    end = time.time()
    print(f"Monthly Moon (1st call/Calc): {end - start:.4f}s")

    start = time.time()
    res2 = get_moon_data_month(pref, year, month)
    end = time.time()
    print(f"Monthly Moon (2nd call/Cache): {end - start:.4f}s")

    # 2. Monthly Sun Data
    start = time.time()
    res3 = get_sun_events_month(pref, year, month)
    end = time.time()
    print(f"Monthly Sun (1st call/Calc): {end - start:.4f}s")

    start = time.time()
    res4 = get_sun_events_month(pref, year, month)
    end = time.time()
    print(f"Monthly Sun (2nd call/Cache): {end - start:.4f}s")

    # 3. Single Day (should be fast now)
    start = time.time()
    res5 = get_moon_data(pref, date_str)
    end = time.time()
    print(f"Single Day Moon (Cached): {end - start:.4f}s (Age: {res5['moon_age']})")

    start = time.time()
    res6 = get_sun_events(pref, date_str)
    end = time.time()
    print(f"Single Day Sun (Cached): {end - start:.4f}s (Rise: {res6['sunrise']})")

    # Data Consistency Check
    assert res1[day]['age'] == res5['moon_age']
    assert res3[day]['sunrise'] == res6['sunrise']
    print("\nData consistency verified!")

if __name__ == "__main__":
    benchmark()
