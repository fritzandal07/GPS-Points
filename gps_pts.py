import csv
import json
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

REJECTS_LOG = "rejects.log"

def haversine(lat1, lon1, lat2, lon2):
    # Calculate distance between two lat/lon points in km
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def parse_row(row):
    try:
        device_id = row['device_id']
        lat = float(row['lat'])
        lon = float(row['lon'])
        timestamp = datetime.fromisoformat(row['timestamp'])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid coordinates")
        return {
            'device_id': device_id,
            'lat': lat,
            'lon': lon,
            'timestamp': timestamp
        }
    except Exception as e:
        with open(REJECTS_LOG, "a") as f:
            f.write(f"Reject row {row}: {e}\n")
        return None

def load_and_clean_data(input_csv):
    points = []
    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            point = parse_row(row)
            if point:
                points.append(point)
    return points

def split_trips(points):
    trips = []
    current_trip = []
    for i, point in enumerate(points):
        if i == 0:
            current_trip.append(point)
            continue

        prev = points[i-1]
        time_diff = (point['timestamp'] - prev['timestamp']).total_seconds() / 60  # minutes
        dist = haversine(prev['lat'], prev['lon'], point['lat'], point['lon'])

        if time_diff > 25 or dist > 2:
            trips.append(current_trip)
            current_trip = [point]
        else:
            current_trip.append(point)
    if current_trip:
        trips.append(current_trip)
    return trips

def compute_trip_stats(trip):
    if len(trip) < 2:
        return {
            'distance_km': 0,
            'duration_min': 0,
            'avg_speed_kmh': 0,
            'max_speed_kmh': 0,
        }
    distance = 0
    max_speed = 0
    for i in range(1, len(trip)):
        prev = trip[i-1]
        curr = trip[i]
        d = haversine(prev['lat'], prev['lon'], curr['lat'], curr['lon'])
        distance += d
        time_diff_hr = (curr['timestamp'] - prev['timestamp']).total_seconds() / 3600
        if time_diff_hr > 0:
            speed = d / time_diff_hr
            if speed > max_speed:
                max_speed = speed
    duration = (trip[-1]['timestamp'] - trip[0]['timestamp']).total_seconds() / 60
    avg_speed = distance / (duration / 60) if duration > 0 else 0
    return {
        'distance_km': round(distance, 3),
        'duration_min': round(duration, 2),
        'avg_speed_kmh': round(avg_speed, 3),
        'max_speed_kmh': round(max_speed, 3),
    }

def save_trip_csv(trip, filename):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['device_id', 'lat', 'lon', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for p in trip:
            writer.writerow({
                'device_id': p['device_id'],
                'lat': p['lat'],
                'lon': p['lon'],
                'timestamp': p['timestamp'].isoformat()
            })

def save_trip_json(trip_stats, filename):
    with open(filename, 'w') as f:
        json.dump(trip_stats, f, indent=2)

def generate_geojson(trips):
    features = []
    colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6']
    for i, trip in enumerate(trips):
        coords = [[p['lon'], p['lat']] for p in trip]
        feature = {
            "type": "Feature",
            "properties": {
                "trip_id": f"trip_{i+1}",
                "color": colors[i % len(colors)]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        }
        features.append(feature)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open("trips.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

def main():
    input_csv = "points.csv"  # change to your downloaded file path
    points = load_and_clean_data(input_csv)
    points.sort(key=lambda x: x['timestamp'])
    trips = split_trips(points)
    for i, trip in enumerate(trips, start=1):
        stats = compute_trip_stats(trip)
        save_trip_csv(trip, f"trip_{i}.csv")
        save_trip_json(stats, f"trip_{i}.json")
    generate_geojson(trips)

if __name__ == "__main__":
    main()
