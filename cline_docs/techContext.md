# Technical Context: Technologies and Environment

## Technologies Used

### Core Technologies
- **Python 3.13**: Primary programming language
- **Immanuel**: Specialized astrological calculation library
  - `immanuel.charts`: Chart calculation
  - `immanuel.tools.ephemeris`: Planetary position calculations
  - `immanuel.const`: Astrological constants
  - `immanuel.setup`: Configuration
  - `immanuel.reports`: Report generation
  - `immanuel.tools.date`: Date conversion utilities
- **NumPy**: Numerical computing for performance-critical operations
- **concurrent.futures**: Parallel processing framework

### Supporting Libraries
- **ZoneInfo**: Timezone handling
- **datetime**: Date and time manipulation
- **json**: Data serialization and deserialization

## Development Setup

### Environment
- **Virtual Environment**: Python venv for dependency isolation
- **Python Version**: 3.13
- **IDE**: Visual Studio Code with Python extensions

### Project Structure
```
astro_calendar_personal_v3/
├── main.py                           # Application entry point
├── src/
│   ├── calculators/                  # Transit calculation modules
│   │   ├── all_transits_parallel.py  # Parallel transit calculation
│   │   ├── astronomical_transits_calculator.py  # Original astronomical calculator
│   │   ├── astronomical_transits_calculator_v2.py  # Enhanced v2 calculator
│   │   ├── astronomical_transits_calculator_v4.py  # Experimental v4 with caching
│   │   ├── calculate_all.py          # Main calculation orchestration
│   │   ├── convert_to_astro_events.py  # Conversion to event objects
│   │   ├── eclipses.py               # Eclipse calculations
│   │   ├── estimate_transit_dates.py  # Transit date estimation
│   │   ├── filter_duplicate_transits.py  # Duplicate filtering
│   │   ├── find_transits_for_planet.py  # Planet-specific transit finding
│   │   ├── lunar_phases.py           # Lunar phase calculations
│   │   ├── optimized_transits_calculator.py  # Optimized calculator variant
│   │   └── transits_calculator_factory.py  # Calculator factory
│   ├── core/                         # Core domain models
│   │   ├── base_event.py             # Base event class
│   │   ├── config.py                 # Configuration
│   │   └── constants.py              # Application constants
│   └── output/                       # Output formatting
│       └── csv_writer.py             # CSV export functionality
└── test_eclipse_calculators.py       # Test suite for eclipse calculations
```

### Build and Run Process
1. Activate virtual environment: `source venv/bin/activate`
2. Run main application: `python main.py`
3. Run tests: `python -m unittest test_eclipse_calculators.py`

## Technical Constraints

### Performance Considerations
- **Computational Intensity**: Astronomical calculations are CPU-intensive.
- **Memory Usage**: Large datasets for multiple planets and long time periods. Caching in V4 might increase memory usage slightly but aims to reduce CPU load.
- **Execution Time**: Balance between accuracy and reasonable calculation times. V4 introduces ephemeris caching (`ephemeris_cache` dictionary) to reduce redundant calculations and improve speed (~20s improvement observed).
- **Caching**: `AstronomicalTransitsCalculatorV4` uses an in-memory dictionary (`ephemeris_cache`) to store results from `ephemeris.planet()` calls, keyed by `(planet_id, jd)`.

### Accuracy Requirements
- **Planetary Positions**: <0.001° accuracy required
- **Aspect Timing**: Precision to the minute for exact aspect times
- **Orb Handling**: Dynamic orbs based on astronomical principles

### Library Dependencies
- **Immanuel Version Compatibility**: Requires specific version for consistent results
- **NumPy Performance**: Optimized for numerical operations

### System Requirements
- **CPU**: Multi-core recommended for parallel processing
- **Memory**: Minimum 4GB RAM recommended
- **Disk Space**: Minimal requirements (~50MB)

## Integration Points
- **Input**: Natal chart data in standard JSON format
- **Output**: 
  - AstroEvent objects for internal processing
  - CSV export for external consumption
  - Potential future API endpoints

## Known Technical Debt
1. **Lunar Transit Handling**: Current implementation suboptimal for the Moon's rapid movement
2. **Error Handling**: Some edge cases not fully covered
3. **Documentation**: Some methods lack comprehensive documentation
4. **Test Coverage**: Not all calculation paths fully tested

## Future Technical Considerations
1. **GPU Acceleration**: Potential for GPU-based calculations for further performance improvements
2. **Web API**: Possible REST API for remote calculations
3. **Caching Layer**: Implement caching for frequently requested calculations
4. **Additional Aspect Types**: Infrastructure to support more aspect types beyond conjunction, opposition, and square
