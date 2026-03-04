from pymongo import MongoClient
from collections import defaultdict
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
from matplotlib.patches import Circle
import numpy as np

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]
reviews_collection = db["reviews"]

# Redis integration
import redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Keyword clusters
CLUSTERS = {
    "Service & Ambience": [
        "friendly", "attentive", "rude", "helpful", "polite", "unfriendly",
        "waiter", "waitress", "staff", "manager", "customer", "service", "efficient", "courteous",
        "ambience", "decor", "lighting", "atmosphere"
    ],
    "Price and Value": [
        "expensive", "overpriced", "cheap", "affordable", "money",
        "worth", "reasonable", "budget", "rip-off", "discount", "deal", "bargain",
        "price", "cost", "value", "robbery", "economic", "premium", "rate"
    ],
    "Time": [
        "time", "wait", "long", "short", "quick", "slow", "fast", "on time",
        "delay", "prompt", "early", "late", "time-consuming", "speed", "instant",
        "dragged", "swift", "lagging", "day", "week", "morning", "evening", "moment"
    ],
    "Location and Accessibility": [
        "easy", "parking", "find", "convenient", "location", "nearby", "close by", "far",
        "away", "remote", "downtown", "uptown", "suburb", "neighborhood", "public",
        "transport", "walk", "distance", "bus", "train", "station", "subway", "access", "drive"
    ],
}

def cache_results(key, data, ttl=3600):
    redis_client.set(key, json.dumps(data), ex=ttl)

def get_cached_results(key):
    cached_data = redis_client.get(key)
    return json.loads(cached_data) if cached_data else None

def process_reviews():
    cache_key = "cache:review_clusters"
    cached_data = get_cached_results(cache_key)
    if cached_data:
        print("Data retrieved from Redis cache.")
        return cached_data["cluster_counts"], cached_data["keyword_counts"]

    cluster_counts = defaultdict(int)
    keyword_counts = defaultdict(lambda: defaultdict(int))

    print("Processing reviews directly in MongoDB using regex search...")

    for cluster_name, keywords in CLUSTERS.items():
        for keyword in keywords:
            # Create a regex query for the current keyword
            query = {"text": {"$regex": f"\\b{keyword}\\b", "$options": "i"}}

            # Count matching documents for the keyword
            count = reviews_collection.count_documents(query)

            if count > 0:
                cluster_counts[cluster_name] += count
                keyword_counts[cluster_name][keyword] += count

    # Cache results in Redis
    cache_results(cache_key, {"cluster_counts": cluster_counts, "keyword_counts": keyword_counts})
    return cluster_counts, keyword_counts


def generate_wordclouds_in_circles(cluster_counts, keyword_counts):
    max_count = max(cluster_counts.values()) if cluster_counts else 1
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")

    positions = [(-0.8, 0.8), (0.8, 0.8), (-0.8, -0.8), (0.8, -0.8)]
    cluster_names = list(cluster_counts.keys())
    total_reviews = sum(cluster_counts.values())
    max_size, min_size = 800, 300

    for i, (cluster_name, keywords) in enumerate(keyword_counts.items()):
        cluster_size = cluster_counts[cluster_name]
        diameter = 0.8 * (cluster_size / max_count)
        radius = diameter / 2
        x, y = positions[i]
        circle = Circle((x, y), radius=radius, edgecolor="black", facecolor="none", lw=2, alpha=0.7)
        ax.add_patch(circle)
        ax.text(x, y + radius + 0.1, f"{cluster_name}\n({cluster_size} Reviews)", ha="center", fontsize=10, color="black")

        mask = np.ones((800, 800), dtype=np.uint8) * 255
        Y, X = np.ogrid[:800, :800]
        center = 400
        mask[(X - center) ** 2 + (Y - center) ** 2 > 400 ** 2] = 255
        mask[(X - center) ** 2 + (Y - center) ** 2 <= 400 ** 2] = 0

        wordcloud = WordCloud(
            width=800, height=800, background_color="white", mask=mask,
            contour_color="black", contour_width=3
        ).generate_from_frequencies(keywords)
        ax.imshow(wordcloud, interpolation="bilinear", extent=[x - radius, x + radius, y - radius, y + radius])

    output_path = "static/images/cluster_wordcloud.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)  # Close the plot to free resources
    print(f"Word cloud saved to {output_path}")
    return output_path



def main():
    cluster_counts, keyword_counts = process_reviews()

    print("Cluster Counts:")
    for cluster, count in cluster_counts.items():
        print(f"{cluster}: {count}")

    generate_wordclouds_in_circles(cluster_counts, keyword_counts)

if __name__ == "__main__":
    main()
