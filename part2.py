import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pymongo import MongoClient
import redis
import json
from datetime import datetime
from collections import defaultdict

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Directory to save generated trendline plots
IMAGE_DIR = "static/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def get_top_reviewed_businesses(city, limit=5):
    # Redis cache key
    cache_key = f"cache:top_reviewed_businesses:{city.lower()}"

    # Check if the result is already cached
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("Fetching results from Redis cache...")
        return json.loads(cached_data)

    # MongoDB query with case-insensitive city search
    print("Fetching results from MongoDB...")
    top_businesses = db.business.find({
        "city": {"$regex": f"^{city}$", "$options": "i"}  # Case-insensitive match
    }).sort("review_count", -1).limit(limit)

    # Convert cursor to list and directly convert ObjectId to string
    top_businesses_list = []
    for business in top_businesses:
        business["_id"] = str(business["_id"])  # Convert ObjectId to string
        top_businesses_list.append(business)

    # Cache the results in Redis with an expiration time (e.g., 1 hour = 3600 seconds)
    redis_client.setex(cache_key, 3600, json.dumps(top_businesses_list))

    return top_businesses_list



def get_reviews_for_business(business_id):
    """Fetch all reviews for a specific business."""
    reviews = db.reviews.find({"business_id": business_id}, {"stars": 1, "date": 1})
    return list(reviews)

def calculate_yearly_avg_stars(reviews):
    """Calculate average stars per year for the given reviews."""
    yearly_reviews = defaultdict(list)
    for review in reviews:
        year = datetime.strptime(review["date"], "%Y-%m-%d").year
        yearly_reviews[year].append(review["stars"])

    avg_stars_per_year = {year: sum(stars) / len(stars) for year, stars in yearly_reviews.items()}
    return dict(sorted(avg_stars_per_year.items()))

def plot_trendlines(city, trends_data):
    """Generate and save trendline plot as an image."""
    plt.figure(figsize=(10, 6))
    for business_name, yearly_avg in trends_data.items():
        years = list(yearly_avg.keys())
        avg_stars = list(yearly_avg.values())
        plt.plot(years, avg_stars, marker='o', label=business_name)

    # Customize the plot
    plt.title(f"User Satisfaction Trendlines for Top 5 Businesses in {city}")
    plt.xlabel("Year")
    plt.ylabel("Average Star Rating")
    plt.legend()
    plt.grid(True)

    # Save the plot as an image
    image_path = os.path.join(IMAGE_DIR, f"trendline_{city.replace(' ', '_')}.png")
    plt.savefig(image_path)  # Save the file
    plt.close()  # Close the figure to free resources
    return image_path
