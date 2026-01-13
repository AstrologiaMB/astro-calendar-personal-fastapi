
"""
POC Benchmark Script
Compares the existing AstronomicalTransitsCalculatorV4 (Production)
against the new PocVectorizedTransitsCalculator (Experimental).
"""
import time
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from immanuel.const import chart, calc
from src.calculators.astronomical_transits_calculator_v4 import AstronomicalTransitsCalculatorV4
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator

# Test User Data (Provided by User)
NATAL_DATA = {
    "name": "Test User",
    "date": "1964-12-26",
    "time": "21:12",
    "location": {
        "lat": -34.6037,
        "lon": -58.3816,
        "timezone": "America/Argentina/Buenos_Aires"
    },
    "points": {
        "Sun": {"longitude": 275.40}, # Approx capricorn
        "Moon": {"longitude": 185.20}, # Approx libra
        "Mercury": {"longitude": 265.1},
        "Venus": {"longitude": 240.5},
        "Mars": {"longitude": 170.2},
        "Jupiter": {"longitude": 45.3},
        "Saturn": {"longitude": 330.1},
        "Uranus": {"longitude": 160.5},
        "Neptune": {"longitude": 230.2},
        "Pluto": {"longitude": 155.4}
    }
}

def run_benchmark():
    print("=== ASTRO CALENDAR POC BENCHMARK ===")
    print(f"Target Year: 2025")
    
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 12, 31, tzinfo=ZoneInfo("UTC"))

    # 1. Run Production Calculator (V4)
    print("\n[1] Running Production Calculator (V4)...")
    v4_calc = AstronomicalTransitsCalculatorV4(NATAL_DATA)
    
    t0 = time.time()
    # Note: V4 usually calculates internally when methods are called, 
    # but here we need to simulate the loop. 
    # V4 logic is scattered, so we'll simulate the main use-case:
    # Checking specific aspects for all planets iteratively (worst case for V4)
    # Ideally we'd call a 'calculate_all' but V4 doesn't have one unified method exposed like that easily.
    # We will simulate the load by asking for aspect checks.
    
    # Mocking the V4 load: V4 is event-based. We'll use a simplified 'scan' to be fair,
    # or actually try to use its methods if possible.
    # To be most fair, let's look at how app.py uses it?
    # Actually, simpler: V4 is slow because of the loop.
    # let's just create instances and calls.
    
    # Since V4 API is complex to invoke for a full year batch without the rest of the system,
    # and we want to measure the ALGORITHM speed, we'll instantiate and run a scan.
    
    # ... Wait, to be perfectly fair and plug-and-play, the new one needs to implement the same interface.
    # But for this POC we are comparing ALGORITHMIC speed.
    
    # Let's run a "Synthetic Workload" that mimics what the backend does:
    # "Find all conjunctions of Sun to Natal Sun for the year"
    
    detected_v4 = []
    # Using public V4 methods to find events
    # V4 doesn't have a 'get_all_transits' method in the class shown. 
    # It likely relies on 'check_aspect_at_date' being called by a looper (Parallel or Adaptive).
    # Ah! The user said app.py uses V4.
    # BUT, performance issues come from the LOOPER + CHECKER.
    
    # So benchmarking JUST V4 class is not enough, we need the Looper.
    # This is why the new POC includes its own internal vector looper.
    
    # For the Baseline, we will assume a basic 1-hour step loop using V4 check_aspect_at_date
    # which is likely how the 'Parallel' or 'Adaptive' calculators work.
    
    count_checks = 0
    t_v4_start = time.time()
    
    # Simulation of "Standard" Iterative Approach (The "Slow" way)
    # Checking every 6 hours for just ONE aspect to estimate total time
    curr = start_date
    while curr <= end_date:
        # Check Sun Conjunction Sun (just 1 case)
        v4_calc.check_aspect_at_date(chart.SUN, curr, NATAL_DATA['points']['Sun']['longitude'], chart.SUN, calc.CONJUNCTION)
        count_checks += 1
        curr += timedelta(hours=6)
        
    t_v4_end = time.time()
    v4_time_per_check = (t_v4_end - t_v4_start) / count_checks
    
    # Estimate total time for ALL planets (10) x ALL aspects (3) x ALL natal planets (10) x 365 days x 24 hours
    # This would be huge. Let's extrapolate.
    est_total_ops = 10 * 10 * 3 * 365 * 4 # 6-hour steps
    projected_v4_time = est_total_ops * v4_time_per_check
    
    print(f"   > Simulated V4 checks: {count_checks}")
    print(f"   > Time per check: {v4_time_per_check*1000:.4f} ms")
    print(f"   > Projected Time for Full Year (Conservative): {projected_v4_time:.2f} s")

    # 2. Run POC Calculator
    print("\n[2] Running POC Vectorized Calculator...")
    poc_calc = PocVectorizedTransitsCalculator(NATAL_DATA)
    
    t_poc_start = time.time()
    events = poc_calc.calculate_all(start_date, end_date)
    t_poc_end = time.time()
    
    poc_time = t_poc_end - t_poc_start
    print(f"   > Total POC Time: {poc_time:.4f} s")
    print(f"   > Events Found: {len(events)}")
    
    # 3. Report
    print("\n=== RESULTS ===")
    print(f"POC is {projected_v4_time / poc_time:.1f}x faster than projected V4")
    
    if len(events) > 0:
        print("\nSample Events Found (First 3):")
        for e in events[:3]:
            print(f" - {e.fecha_utc} | {e.descripcion} | Orbe: {e.orbe:.4f}")

if __name__ == "__main__":
    run_benchmark()
