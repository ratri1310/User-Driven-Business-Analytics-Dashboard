import folium
from pymongo import MongoClient
import redis
import json
import os

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]
business_collection = db["business"]

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

STATIC_MAPS_DIR = "static/maps"
os.makedirs(STATIC_MAPS_DIR, exist_ok=True)

# Fetch data from MongoDB and cache in Redis
def get_city_business_distribution():
    cache_key = "cache:city_business_distribution"
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("Data retrieved from Redis cache.")
        return json.loads(cached_data)

    # MongoDB aggregation query
    pipeline = [
        {"$group": {"_id": "$city", "business_count": {"$sum": 1}}},
        {"$sort": {"business_count": -1}},
        {"$limit": 100}  # Top 100 cities
    ]
    results = list(business_collection.aggregate(pipeline))

    # Cache the results in Redis
    redis_client.set(cache_key, json.dumps(results), ex=3600)  # Cache for 1 hour
    return results

# Normalize business count for display purposes
def normalize_counts(city_data):
    counts = [city["business_count"] for city in city_data]
    min_count, max_count = min(counts), max(counts)

    for city in city_data:
        # Normalize business_count to range [0, 1]
        city["normalized_count"] = (city["business_count"] - min_count) / (max_count - min_count)
    return city_data

# Plot the Arizona map with normalized counts and city names
def plot_arizona_map(city_data):
    # Create a Folium map centered on Arizona
    arizona_map = folium.Map(location=[34.0489, -111.0937], zoom_start=6)

    # Add markers for each city
    for city in city_data:
        city_name = city["_id"]
        business_count = city["business_count"]
        normalized_count = city["normalized_count"]

        city_location = business_collection.find_one({"city": city_name}, {"latitude": 1, "longitude": 1, "_id": 0})
        if city_location and "latitude" in city_location and "longitude" in city_location:
            latitude = city_location["latitude"]
            longitude = city_location["longitude"]

            folium.Marker(
                location=[latitude, longitude],
                popup=f"{city_name}: {business_count} businesses (Normalized: {normalized_count:.2f})",
                tooltip=f"{city_name}: {business_count} businesses",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(arizona_map)

    # Save the map to the static folder
    # Save the map to 'static/maps' directory
    map_filename = "arizona_business_distribution.html"
    map_path = os.path.join(STATIC_MAPS_DIR, map_filename)
    arizona_map.save(map_path)
    print(f"Map has been saved as '{map_path}'.")
    return map_filename  # Return only the filename

def main():
    # Get city business data
    city_data = get_city_business_distribution()

    # Normalize business counts for display
    city_data = normalize_counts(city_data)

    # Plot the map
    plot_arizona_map(city_data)

if __name__ == "__main__":
    main()
