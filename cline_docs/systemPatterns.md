# System Patterns: Architecture and Design

## How the System is Built
The Astrological Calendar application follows a modular architecture with clear separation of concerns:

1. **Core Calculation Layer**: Handles the astronomical calculations and mathematical operations
2. **Event Processing Layer**: Transforms raw astronomical data into meaningful astrological events
3. **Output Generation Layer**: Formats and presents the events to users

The system is primarily implemented in Python, leveraging specialized astronomical libraries for the core calculations.

## Key Technical Decisions

### 1. Astronomical Calculation Approach
- **Decision**: Use the Immanuel library (`immanuel.charts`, `immanuel.tools.ephemeris`) for core astronomical calculations
- **Rationale**: Provides high-precision ephemeris data and astronomical functions specifically designed for astrological applications
- **Impact**: Ensures accurate planetary positions and aspects, at the cost of some computational overhead

### 2. Adaptive Sampling Strategy
- **Decision**: Implement variable-density sampling based on planetary speed, aspect type, and critical periods
- **Rationale**: Different planets and aspects require different sampling densities to ensure accurate detection
- **Impact**: Balances computational efficiency with detection accuracy

### 3. Binary Search for Exact Aspect Times
- **Decision**: Use binary search algorithm to pinpoint exact times of aspects
- **Rationale**: Provides mathematical precision without requiring excessive sampling
- **Impact**: Significantly improves accuracy of aspect timing with minimal performance impact

### 4. Parallel Processing
- **Decision**: Use `concurrent.futures.ThreadPoolExecutor` for parallel planet processing
- **Rationale**: Transit calculations for different planets are independent and can be parallelized
- **Impact**: Improves performance on multi-core systems

### 5. Dynamic Universal Orbs
- **Decision**: Implement orbs that adjust based on planet, aspect type, and other astronomical factors
- **Rationale**: Different planet-aspect combinations require different orb sizes for optimal detection
- **Impact**: Improves detection of challenging aspects while reducing false positives

## Architecture Patterns

### 1. Factory Pattern
- **Implementation**: `transits_calculator_factory.py` creates appropriate calculator instances
- **Purpose**: Allows selection of different calculation strategies (standard, optimized, astronomical)

### 2. Strategy Pattern
- **Implementation**: Different calculator classes implement the same interface but with different algorithms
- **Purpose**: Enables switching between calculation approaches based on user needs or system capabilities

### 3. Builder Pattern
- **Implementation**: Step-by-step construction of complex transit events from raw astronomical data
- **Purpose**: Separates the construction process from the representation

### 4. Pipeline Pattern
- **Implementation**: Multi-stage processing flow from raw calculations to filtered and formatted events
- **Purpose**: Enables clean separation of concerns and modular processing steps

### 5. Repository Pattern
- **Implementation**: Abstraction layer for data storage and retrieval
- **Purpose**: Isolates the data layer from the business logic

### 6. Caching Pattern (In-Memory Dictionary)
- **Implementation**: `AstronomicalTransitsCalculatorV4` uses an instance variable dictionary (`self.ephemeris_cache`) to store results of `ephemeris.planet()` calls.
- **Purpose**: Reduce redundant, computationally expensive ephemeris calculations for the same planet and Julian date within a single run, improving performance.
- **Scope**: Cache is per-instance and lives only for the duration of the calculator object's life.

## Code Organization
- `src/calculators/`: Contains all calculation-related classes and functions
- `src/core/`: Core domain models and constants
- `src/output/`: Output formatting and generation
- `main.py`: Application entry point and orchestration

## Error Handling Strategy
The system employs defensive programming with specific error handling for:
1. Astronomical calculation edge cases
2. Invalid input data
3. Performance degradation scenarios

Each calculator method includes appropriate error handling and fallback mechanisms to ensure robustness.
