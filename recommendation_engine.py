#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
data = pd.read_csv('recommendation_data.csv')

# Create user-item matrix
user_item_matrix = pd.pivot_table(data, values='rating', index='user_id', columns='item_id', aggfunc=np.mean)

# Implement collaborative filtering
def recommend_items(user_id, num_recommendations):
    # Get top N items for the given user
    top_n_items = user_item_matrix.loc[user_id].nlargest(num_recommendations)
    
    # Calculate cosine similarity with other users who have rated these items
    similar_users = []
    for item in top_n_items.index:
        similar_users.append((item, cosine_similarity(user_item_matrix.drop(item).T, top_n_items[item].values)))
    similar_users.sort(key=lambda x: -x[1])

    # Recommend items based on the most similar users
    recommended_items = set()
    for i in range(num_recommendations):
        recommended_items.add(similar_users[i][0])
    
    return list(recommended_items)

# Implement content-based filtering
def recommend_items_content(user_item_matrix, user_id, num_recommendations):
    # Get top N items for the given user
    top_n_items = user_item_matrix.loc[user_id].nlargest(num_recommendations)
    
    # Calculate cosine similarity with other users who have rated similar items
    similar_users = []
    for item in top_n_items.index:
        similar_users.append((item, cosine_similarity(user_item_matrix.drop(item).T, top_n_items[item].values)))
    similar_users.sort(key=lambda x: -x[1])

    # Recommend items based on the most similar users
    recommended_items = set()
    for i in range(num_recommendations):
        recommended_items.add(similar_users[i][0])
    
    return list(recommended_items)

if __name__ == "__main__":
    user_id = 123
    num_recommendations = 5
    print("Recommended items for user {}:".format(user_id))
    print(recommend_items(user_id, num_recommendations))

