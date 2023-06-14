import sqlite3
from scipy.stats import norm
import numpy as np
from collections import Counter
import math


conn = sqlite3.connect('my_db.db')
c = conn.cursor()


# Get user profile data: Most used apps, most searched topics, most typed topics
def get_profile_data(data):
    
    if not data:
        return []
    
    # Calculate the mean and standard deviation of the number of searches for each topic
    search_counts = [t[1] for t in data]
    search_mean = np.mean(search_counts)
    search_stddev = np.std(search_counts)
    
    # Set the confidence level to 90%
    confidence_level = 0.9
    
    # Calculate the margin of error using the standard error of the mean
    z_score = norm.ppf(1 - ((1 - confidence_level) / 2))
    margin_of_error = z_score * (search_stddev / np.sqrt(len(search_counts)))
    
    # Calculate the confidence interval
    lower_bound = search_mean - margin_of_error
    upper_bound = search_mean + margin_of_error

    # Find the topic(s) with the highest search count within the confidence interval
    new_topics = []
    for t in data:
        if t[1] >= lower_bound:
            new_topics.append(t[0])
    
    return new_topics


def get_data_percentage(data):
    total_count = sum([count for _, count in data])
    percentage_tuples = []
    for word, count in data:
        percentage = (count / total_count) * 100
        percentage_tuples.append((word, percentage))
    return percentage_tuples


# Create user profiles
def create_profile(apps, websites, texts):

    apps = [(app[1], app[2]) for app in apps]
    texts = [(text[1], text[2]) for text in texts]
    websites = [web[2] for web in websites]
    websites = [(t, websites.count(t)) for t in set(websites)]

    a_data = get_profile_data(apps)
    w_data = get_profile_data(websites)
    t_data = get_profile_data(texts)

    return a_data, w_data, t_data


# Run anomaly verification on given topic using confidence interval
def conf_detect_anomaly(topic, topic_list, alpha=0.05):

    n = len(topic_list)
    if n == 0:
        return True
    count_topic = Counter(topic_list)[topic]
    p = count_topic / n
    se = math.sqrt(p * (1 - p) / n)
    z = 1.96 # corresponds to 95% confidence interval
    ci = (p - z*se, p + z*se)

    if ci[0] <= 1/n or ci[1] >= 1 - 1/n:
        return True
    else:
        return False
