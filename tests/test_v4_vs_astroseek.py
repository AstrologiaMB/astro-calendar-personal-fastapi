import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import os
import sys

# Add project root to the Python path to allow imports from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Assuming calculators and constants are accessible from src
# Adjust imports based on actual project structure if needed
from src.calculators.astronomical_transits_calculator_v4 import (
    AstronomicalTransitsCalculatorV4,
    ASPECT_NAMES,  # Import needed dictionary
    PLANET_NAMES   # Import needed dictionary
)
from src.core.constants import EventType, AstronomicalConstants
from immanuel.const import chart, calc

# --- Configuration ---
BENCHMARK_FILE = 'tests/data/astroseek_benchmark_2025.csv'
TARGET_YEAR = 2025
# IMPORTANT: Define the timezone Astroseek used for the export
# Confirmed as America/Buenos_Aires by user
BENCHMARK_TIMEZONE = ZoneInfo("America/Buenos_Aires")
# Tolerance for comparing event times
TIME_TOLERANCE = timedelta(minutes=10) # Allow +/- 10 minutes difference

# --- Mappings ---
# Map Astroseek planet names/abbreviations to our internal chart constants
PLANET_MAP_ASTROSEEK = {
    "Sun": chart.SUN,
    "Moon": chart.MOON,
    "Mercury": chart.MERCURY,
    "Merc.": chart.MERCURY, # Abbreviation
    "Venus": chart.VENUS,
    "Mars": chart.MARS,
    "Jupiter": chart.JUPITER,
    "Saturn": chart.SATURN,
    "Uranus": chart.URANUS,
    "Neptune": chart.NEPTUNE,
    "Pluto": chart.PLUTO,
    # Add mappings for natal points if they appear differently in the file
    # e.g., "Ascendant": "ASC", "MC": "MC"
}

# Map Astroseek aspect names to our internal calc constants
ASPECT_MAP_ASTROSEEK = {
    "conjunction": calc.CONJUNCTION,
    "opposition": calc.OPPOSITION,
    "square": calc.SQUARE,
    # Add other aspects only if needed for filtering, but comparison focuses on the above
    "trine": calc.TRINE,
    "sextile": calc.SEXTILE,
}

# Aspects we want to compare
TARGET_ASPECTS_INTERNAL = {calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE}
TARGET_ASPECTS_ASTROSEEK = {"conjunction", "opposition", "square"}

# --- Helper Functions ---
def parse_benchmark_datetime(date_str: str, time_str: str, year: int, tz: ZoneInfo) -> datetime:
    """Parses the Astroseek date and time string."""
    try:
        # Combine, add year, and parse
        dt_str = f"{date_str} {year} {time_str}"
        # Example format: "Jan 2 2025 18:07"
        dt_naive = datetime.strptime(dt_str, "%b %d %Y %H:%M")
        # Localize to the benchmark timezone, then convert to UTC for comparison
        dt_localized = dt_naive.replace(tzinfo=tz)
        return dt_localized.astimezone(ZoneInfo("UTC"))
    except ValueError as e:
        print(f"Error parsing date/time: {date_str} {time_str} - {e}")
        return None

def parse_event_description(desc: str) -> tuple | None:
    """Parses the event description string from Astroseek."""
    # Example: "Transit Mercury  - square -  Mars"
    match = re.match(r"Transit\s+(.+?)\s+-\s+(.+?)\s+-\s+(.+)", desc.strip())
    if match:
        p1_name = match.group(1).strip()
        aspect_name = match.group(2).strip().lower() # Lowercase for consistent mapping
        p2_name = match.group(3).strip()

        # Map names to internal constants
        p1_id = PLANET_MAP_ASTROSEEK.get(p1_name)
        aspect_id = ASPECT_MAP_ASTROSEEK.get(aspect_name)
        p2_id = PLANET_MAP_ASTROSEEK.get(p2_name)

        if p1_id is not None and aspect_id is not None and p2_id is not None:
            return p1_id, aspect_id, p2_id
        else:
            # Print warnings for unmapped items
            if p1_id is None: print(f"Warning: Unmapped transit planet '{p1_name}'")
            if aspect_id is None: print(f"Warning: Unmapped aspect '{aspect_name}'")
            if p2_id is None: print(f"Warning: Unmapped natal planet '{p2_name}'")
            return None
    else:
        # Handle other description formats if necessary
        # print(f"Warning: Could not parse description '{desc}'")
        pass # Ignore lines that don't match the expected transit format
    return None

# --- Main Comparison Logic ---

def load_astroseek_benchmark(filepath: str, year: int, tz: ZoneInfo) -> list:
    """Loads and parses the Astroseek benchmark CSV."""
    benchmark_events = []
    print(f"Loading benchmark file: {filepath}")
    if not os.path.exists(filepath):
        print(f"Error: Benchmark file not found at {filepath}")
        return benchmark_events

    try:
        # Use utf-8-sig to handle potential BOM
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            for i, row in enumerate(reader):
                if len(row) < 2: # Need at least date/time and description
                    # print(f"Skipping row {i+1}: Insufficient columns {row}")
                    continue

                # Combine date and time from the first column
                dt_part = row[0].strip()
                # Find the last comma to separate date and time
                last_comma_index = dt_part.rfind(',')
                if last_comma_index == -1:
                    # print(f"Skipping row {i+1}: Cannot split date/time in '{dt_part}'")
                    continue
                date_str = dt_part[:last_comma_index].strip()
                time_str = dt_part[last_comma_index+1:].strip()

                description = row[1].strip()

                dt_utc = parse_benchmark_datetime(date_str, time_str, year, tz)
                if dt_utc is None:
                    # print(f"Skipping row {i+1}: Could not parse datetime")
                    continue

                parsed_desc = parse_event_description(description)
                if parsed_desc is None:
                    # print(f"Skipping row {i+1}: Could not parse description '{description}'")
                    continue

                p1_id, aspect_id, p2_id = parsed_desc

                # Filter for target aspects only
                if aspect_id in TARGET_ASPECTS_INTERNAL:
                    benchmark_events.append({
                        "datetime_utc": dt_utc,
                        "transit_planet": p1_id,
                        "aspect": aspect_id,
                        "natal_planet": p2_id,
                        "matched": False # Flag for comparison tracking
                    })
    except FileNotFoundError:
        print(f"Error: Benchmark file not found at {filepath}")
    except Exception as e:
        print(f"Error reading benchmark file {filepath}: {e}")

    print(f"Loaded {len(benchmark_events)} relevant benchmark events.")
    return benchmark_events

def run_v4_calculator(year: int, natal_data: dict) -> list:
    """Runs the V4 calculator and filters results."""
    print("Running AstronomicalTransitsCalculatorV4...")
    # TODO: Replace with actual natal data loading/definition
    if not natal_data:
         print("Error: Natal data is missing for V4 calculation.")
         # Use placeholder if necessary for testing script structure
         # This needs to be the SAME data used for the benchmark!
         placeholder_natal_data = {
             'datetime': '1990-01-01T12:00:00',
             'tz_str': 'UTC',
             'location': {'latitude': 0, 'longitude': 0, 'altitude': 0, 'timezone': 'UTC'},
             'points': { # Example positions - REPLACE WITH ACTUAL DATA
                 'Sun': {'longitude': 280.0}, 'Moon': {'longitude': 15.0},
                 'Mercury': {'longitude': 290.0}, 'Venus': {'longitude': 310.0},
                 'Mars': {'longitude': 250.0}, 'Jupiter': {'longitude': 95.0},
                 'Saturn': {'longitude': 295.0}, 'Uranus': {'longitude': 275.0},
                 'Neptune': {'longitude': 285.0}, 'Pluto': {'longitude': 225.0}
             },
             'angles': { # Example angles - REPLACE WITH ACTUAL DATA
                 'ASC': {'longitude': 0.0}, 'MC': {'longitude': 270.0}
             }
         }
         print("Warning: Using placeholder natal data for V4.")
         natal_data_to_use = placeholder_natal_data
    else:
         natal_data_to_use = natal_data

    calculator = AstronomicalTransitsCalculatorV4(natal_data_to_use)
    start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=calculator.user_timezone)
    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=calculator.user_timezone)

    try:
        v4_events_raw = calculator.calculate_all(start_date=start_date, end_date=end_date)
    except Exception as e:
        print(f"Error running V4 calculator: {e}")
        return []

    # Filter V4 events for target aspects and convert structure for comparison
    v4_events_filtered = []
    for event in v4_events_raw:
        # Map aspect name back to internal constant if needed, or use internal constant directly
        aspect_name_map_reverse = {v: k for k, v in ASPECT_NAMES.items()}
        aspect_id = aspect_name_map_reverse.get(event.tipo_aspecto)

        # Map planet names back to internal constants
        planet_name_map_reverse = {v: k for k, v in PLANET_NAMES.items()}
        p1_id = planet_name_map_reverse.get(event.planeta1)
        p2_id = planet_name_map_reverse.get(event.planeta2)
        # Handle angles if necessary
        if event.planeta2 in ['ASC', 'MC', 'DESC', 'IC']:
             p2_id = event.planeta2 # Keep angle names as strings if that's how they are stored

        if aspect_id in TARGET_ASPECTS_INTERNAL and p1_id is not None and p2_id is not None:
            v4_events_filtered.append({
                "datetime_utc": event.fecha_utc,
                "transit_planet": p1_id,
                "aspect": aspect_id,
                "natal_planet": p2_id,
                "matched": False # Flag for comparison tracking
            })

    print(f"V4 calculator produced {len(v4_events_filtered)} relevant events.")
    return v4_events_filtered

def compare_results(benchmark_events: list, v4_events: list, tolerance: timedelta):
    """Compares benchmark events against V4 results."""
    print("\n--- Comparison Report ---")
    matches = 0
    missing_in_v4 = []
    time_mismatches = []

    # Sort both lists by time for potentially easier matching
    benchmark_events.sort(key=lambda x: x['datetime_utc'])
    v4_events.sort(key=lambda x: x['datetime_utc'])

    for bench_event in benchmark_events:
        found_match = False
        best_match_v4_event = None
        smallest_diff = tolerance + timedelta(seconds=1) # Initialize with value > tolerance

        for v4_event in v4_events:
            # Check if V4 event is already matched
            if v4_event['matched']:
                continue

            # Check for matching planets and aspect
            if (bench_event['transit_planet'] == v4_event['transit_planet'] and
                bench_event['natal_planet'] == v4_event['natal_planet'] and
                bench_event['aspect'] == v4_event['aspect']):

                # Check time difference
                time_diff = abs(bench_event['datetime_utc'] - v4_event['datetime_utc'])

                if time_diff <= tolerance:
                    # Potential match found, check if it's the closest one so far
                    if time_diff < smallest_diff:
                         smallest_diff = time_diff
                         best_match_v4_event = v4_event
                         found_match = True
                elif time_diff <= tolerance * 3: # Check for slightly larger mismatches
                     # Potential time mismatch, record it but keep looking for exact match
                     time_mismatches.append({
                         "benchmark": bench_event,
                         "v4": v4_event,
                         "diff": time_diff
                     })


        if found_match and best_match_v4_event:
            matches += 1
            bench_event['matched'] = True
            best_match_v4_event['matched'] = True
            # Remove potential time mismatches involving the matched v4 event
            time_mismatches = [tm for tm in time_mismatches
                               if tm['v4'] != best_match_v4_event]
        else:
            # No match within tolerance found for this benchmark event
            missing_in_v4.append(bench_event)

    # Events in V4 that were not matched to any benchmark event
    extra_in_v4 = [v4 for v4 in v4_events if not v4['matched']]

    # --- Output Summary ---
    print(f"\nTotal Benchmark Events (Target Aspects): {len(benchmark_events)}")
    print(f"Total V4 Events (Target Aspects): {len(v4_events)}")
    print(f"Matches within {tolerance}: {matches}")

    if missing_in_v4:
        print(f"\nEvents MISSING in V4 ({len(missing_in_v4)}):")
        for event in missing_in_v4[:20]: # Show first 20
             p1 = PLANET_NAMES.get(event['transit_planet'], str(event['transit_planet']))
             p2 = PLANET_NAMES.get(event['natal_planet'], str(event['natal_planet']))
             asp = ASPECT_NAMES.get(event['aspect'], str(event['aspect']))
             print(f"  - {event['datetime_utc'].strftime('%Y-%m-%d %H:%M')} UTC: Transit {p1} {asp} {p2}")
        if len(missing_in_v4) > 20: print("  ...")

    if extra_in_v4:
        print(f"\nEvents EXTRA in V4 ({len(extra_in_v4)}):")
        for event in extra_in_v4[:20]: # Show first 20
             p1 = PLANET_NAMES.get(event['transit_planet'], str(event['transit_planet']))
             p2 = PLANET_NAMES.get(event['natal_planet'], str(event['natal_planet']))
             asp = ASPECT_NAMES.get(event['aspect'], str(event['aspect']))
             print(f"  - {event['datetime_utc'].strftime('%Y-%m-%d %H:%M')} UTC: Transit {p1} {asp} {p2}")
        if len(extra_in_v4) > 20: print("  ...")

    # Report significant time mismatches (those not resolved by a closer match)
    final_mismatches = []
    for tm in time_mismatches:
         # Ensure both events involved weren't actually matched later
         if not tm['benchmark']['matched'] and not tm['v4']['matched']:
              final_mismatches.append(tm)

    # Deduplicate mismatches (same pair might be reported twice)
    unique_mismatches = []
    seen_pairs = set()
    for tm in final_mismatches:
        pair_key = tuple(sorted((str(tm['benchmark']), str(tm['v4']))))
        if pair_key not in seen_pairs:
            unique_mismatches.append(tm)
            seen_pairs.add(pair_key)


    if unique_mismatches:
        print(f"\nPotential Time MISMATCHES > {tolerance} ({len(unique_mismatches)}):")
        for mismatch in unique_mismatches[:20]: # Show first 20
            bench_event = mismatch['benchmark']
            v4_event = mismatch['v4']
            p1 = PLANET_NAMES.get(bench_event['transit_planet'], str(bench_event['transit_planet']))
            p2 = PLANET_NAMES.get(bench_event['natal_planet'], str(bench_event['natal_planet']))
            asp = ASPECT_NAMES.get(bench_event['aspect'], str(bench_event['aspect']))
            print(f"  - Bench: {bench_event['datetime_utc'].strftime('%Y-%m-%d %H:%M')} | V4: {v4_event['datetime_utc'].strftime('%Y-%m-%d %H:%M')} | Diff: {mismatch['diff']} | Event: {p1} {asp} {p2}")
        if len(unique_mismatches) > 20: print("  ...")

    print("\n--- End Comparison Report ---")


# --- Script Execution ---
import json # Add json import for loading natal data

# --- Script Execution ---
if __name__ == "__main__":
    # Load the actual natal data used for the benchmark from the specified JSON file
    natal_data_path = 'output/carta_natal_lmv1.json'
    actual_natal_data = {}
    print(f"--- Loading Natal Data from: {natal_data_path} ---")
    try:
        with open(natal_data_path, 'r') as f:
            actual_natal_data = json.load(f)
        print("Natal data loaded successfully.")
    except FileNotFoundError:
        print(f"Error: Natal data file not found at {natal_data_path}")
        print("Comparison cannot proceed without natal data.")
        exit() # Exit if natal data cannot be loaded
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {natal_data_path}")
        print("Comparison cannot proceed without natal data.")
        exit() # Exit if natal data is invalid
    except Exception as e:
        print(f"An unexpected error occurred loading natal data: {e}")
        exit()

    print("\n--- Starting V4 vs Astroseek Benchmark Comparison ---")
    print(f"Target Year: {TARGET_YEAR}")
    print(f"Benchmark File: {BENCHMARK_FILE}")
    print(f"Benchmark Timezone: {BENCHMARK_TIMEZONE}")
    print(f"Time Tolerance: +/- {TIME_TOLERANCE}")

    benchmark_data = load_astroseek_benchmark(BENCHMARK_FILE, TARGET_YEAR, BENCHMARK_TIMEZONE)
    v4_results = run_v4_calculator(TARGET_YEAR, actual_natal_data)

    if benchmark_data and v4_results:
        compare_results(benchmark_data, v4_results, TIME_TOLERANCE)
    elif not benchmark_data:
        print("\nComparison skipped: Could not load benchmark data.")
    else:
        print("\nComparison skipped: Could not get V4 results.")

    print("\n--- Comparison Script Finished ---")
