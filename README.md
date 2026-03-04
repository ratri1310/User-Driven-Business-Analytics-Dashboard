# **Final Project Repository for "User-Driven Business Analytics and Insights Dashboard" **

**Group Members:**  
- Ratri Mukherjee  
- Shailesh Dahal  
- Yan Liu  

---

## **Databases Used**

- **MongoDB**: Main storage and query database. 
- **Redis**: Used as a cache to retrieve results faster.

### **How Caching Works**  
- For **new queries**, results are fetched from MongoDB, cached in Redis, and displayed.  
- For **repeated queries**, results are displayed directly from the Redis cache.  
- **Case-Insensitive Search**: MongoDB supports case-insensitive text search, allowing input in any case (Upper/Lower/Mixed).

---

## **Dataset**

- **Source**: We have used Yelp Business Review Dataset for the project. For computational convenience, we have used an academic version of The Yelp dataset that includes business and review details for businesses in Arizona, USA. [Yelp Phoenix Academic Dataset](https://github.com/knowitall/yelp-dataset-challenge/tree/master/data/yelp_phoenix_academic_dataset)  

---

## **Setup Instructions**
This project uses Python 3.10 . 

### **Installing Requirements**

Use the following command to install dependencies:  
```bash
pip install -r requirements.txt

### **Installing Requirements**
### **Before Running the Program**

Modify lines **51**, **101**, and **141** in `main.py`:  
Replace `/usr/local/bin/python3.10` with your custom Python path or name (e.g., `python` or `python3`).

This will start the Flask-based web server at http://127.0.0.1:5001/

![Index Page](static/images_doc/index_page.png)

The index page contains 6 menus which user can select one at a time. Each subsequent pages follow the menus in index page and have provision to go back to index page.

Choices:
1. Identify Most Active User
    This page evaluates the most active user in the database. In the backend, it calls program part1.py. The _id of top 5 users based on their review count are displayed in descending order.

2. Identify Trend in User Satisfaction
    This page evaluates the trend in user satisfaction. User can enter the name of city for which they want to visualize user satisfaction trend. For the entered city name, it plots the trend graph of average user rating of top 5 businesses based on review count for that city from min_year to max_year available in review dataset. Y-axis shows the average user rating in particular year(=sum_reviews/n for that year) and X-axis shows the range of year available in review dataset. Multiple trendlines represent the top 5 businesses based on review count. The main code used for this section in backend is part2.py. 

3. Cluster Review Themes
    This page shows the four major clusters of focus area of user reviews. We created a dictionary of words for 4 different groups: Service & Ambience, Price & Value, Time, Location & Accessibility. The user reviews are clustered based on those keywords. Their cluster size and the major keywords are displayed as wordcloud. This part does not take any input from user and runs part3.py in backend.

4. Geographical Analysis
    This page shows the map and pinned location for the top 10 businesses in the city that user wishes to see. After the user enters the city name, s/he can choose from one of the two available options: "Sort by Average Stars" and "Sort by Number of Reviews". Based on the sort criteria, top 10 businesses in that city are queried in the database and displayed in map. If we click on the pins, it will show more details of that business. This page calls part4.py in backend.

5. Business Distribution
    This page displays the number of businesses in different cities in map. This does not need user input and directly calls part5.py in the backend. 

6. Geospatial Analysis (Nearby Business Search)
    This page displays the nearest businesses from a desired location in map. User has provision to enter the lattitude and longitude of the center location. Based on the boundary radius entered by user in miles and the minimum star rating criteria, it pins the top 10 businesses in map.
