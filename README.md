# GPS Trip Processing Script

## Installation
Ensure Python 3 is installed on your system. No external libraries are needed.

## How to run
1. run `pipenv shell`
2. Place your input CSV as `points.csv` in the script directory.
3. Run the script with `python gps_pts.py`.
4. Outputs will be generated in the same directory:
   - `trip_*.csv` — points per trip
   - `trip_*.json` — trip stats
   - `rejects.log` — invalid rows
   - `trips.geojson` — GeoJSON visualization of all trips

Modify `points.csv` variable in the script if needed.
