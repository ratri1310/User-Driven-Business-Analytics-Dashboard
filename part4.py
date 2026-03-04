import folium
from pymongo import MongoClient
import redis
import json
from geopy.geocoders import Nominatim
import ssl
import certifi
import os

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]
business_collection = db["business"]

# Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Geolocator with SSL fix
geolocator = Nominatim(user_agent="geoapi", ssl_context=ssl.create_default_context(cafile=certifi.where()))

# Ensure static maps directory exists
os.makedirs("static/maps", exist_ok=True)

def get_city_coordinates(city):
    try:
        city = city.strip()
        location = geolocator.geocode(f"{city}, Arizona")
        if location:
            return (location.latitude, location.longitude)
        return (34.0489, -111.0937)  # Default to Arizona center
    except Exception:
        return (34.0489, -111.0937)

def get_top_businesses_in_city(city_name, sort_by):
    sort_field = "stars" if sort_by == 1 else "review_count"
    cache_key = f"cache:top_businesses:{city_name.lower()}:{sort_by}"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    businesses = business_collection.find(
        {"city": {"$regex": f"^{city_name}$", "$options": "i"}},
        {"name": 1, "stars": 1, "review_count": 1, "latitude": 1, "longitude": 1, "_id": 0}
    ).sort(sort_field, -1).limit(10)

    businesses_list = list(businesses)
    redis_client.set(cache_key, json.dumps(businesses_list), ex=3600)
    return businesses_list

def generate_city_map(city_name, businesses):
    city_coordinates = get_city_coordinates(city_name)
    city_map = folium.Map(location=city_coordinates, zoom_start=12)

    for rank, business in enumerate(businesses, start=1):
        latitude = business.get("latitude", city_coordinates[0])
        longitude = business.get("longitude", city_coordinates[1])
        popup_text = f"""
            <b>Rank:</b> {rank}<br>
            <b>Business:</b> {business['name']}<br>
            <b>Stars:</b> {business['stars']}<br>
            <b>Reviews:</b> {business['review_count']}
        """
        folium.Marker(
            location=(latitude, longitude),
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{rank}. {business['name']}"
        ).add_to(city_map)

    map_filename = f"static/maps/{city_name}_businesses_map.html"
    city_map.save(map_filename)
    return map_filename
