import os
import folium
from pymongo import MongoClient
import redis
import json

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]
business_collection = db["business"]

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Ensure the directory 'static/maps' exists
STATIC_MAPS_DIR = "static/maps"
os.makedirs(STATIC_MAPS_DIR, exist_ok=True)

# Fetch top businesses within a given radius and minimum rating
def get_top_businesses(user_lat, user_lon, radius, min_rating, limit=10):
    cache_key = f"cache:top_businesses:{user_lat}:{user_lon}:{radius}:{min_rating}:{limit}"
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("Data retrieved from Redis cache.")
        return json.loads(cached_data)

    # Query to find top businesses
    query = {
        "stars": {"$gte": min_rating},  # Minimum star rating
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [user_lon, user_lat]},
                "$maxDistance": radius  # Radius in meters
            }
        }
    }

    # Fetch results
    results = list(
        business_collection.find(query, {"name": 1, "stars": 1, "latitude": 1, "longitude": 1})
        .limit(limit)
    )

    for business in results:
        if "_id" in business:
            business["_id"] = str(business["_id"])

    # Cache results
    redis_client.set(cache_key, json.dumps(results), ex=3600)
    return results

# Generate map with businesses
def plot_business_map(user_lat, user_lon, businesses):
    business_map = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # Add user's location marker
    folium.Marker(
        location=[user_lat, user_lon],
        popup="Your Location",
        icon=folium.Icon(color="red", icon="user")
    ).add_to(business_map)

    # Add business markers
    for business in businesses:
        folium.Marker(
            location=[business["latitude"], business["longitude"]],
            popup=f"{business['name']}: {business['stars']} stars",
            tooltip=f"{business['name']} ({business['stars']} stars)",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(business_map)

    # Save map to 'static/maps'
    map_filename = "user_business_map.html"
    map_path = os.path.join(STATIC_MAPS_DIR, map_filename)
    business_map.save(map_path)
    return f"maps/{map_filename}"  # Path relative to 'static'
