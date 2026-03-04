from pymongo import MongoClient
import redis
import json

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["project"]

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Step 4.1: Identify Active Users
def get_top_active_users():
    # MongoDB aggregation query to find top active users
    top_users = db.reviews.aggregate([
        {"$group": {"_id": "$user_id", "review_count": {"$sum": 1}}},
        {"$sort": {"review_count": -1}},
        {"$limit": 5}
    ])

    # Convert cursor to a list
    top_users_list = list(top_users)

    # Save to Redis
    redis_client.set("cache:active_users", json.dumps(top_users_list))

    return top_users_list

# Fetch and print top active users
def main():
    active_users = get_top_active_users()

    # Print only JSON output (no extra text)
    print(json.dumps(active_users))  # Ensures valid JSON format

if __name__ == "__main__":
    main()
