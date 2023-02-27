import sqlite3
conn = sqlite3.connect('my_db.db')
c = conn.cursor()

import numpy as np
from scipy.stats import t, norm

def get_profile_data(data):
    # Calculate the mean and standard deviation of the number of searches for each topic
    search_counts = [t[1] for t in data]
    search_mean = np.mean(search_counts)
    search_stddev = np.std(search_counts)
    
    # Set the confidence level to 95%
    confidence_level = 0.95
    
    # Calculate the margin of error using the standard error of the mean
    z_score = norm.ppf(1 - ((1 - confidence_level) / 2))
    margin_of_error = z_score * (search_stddev / np.sqrt(len(search_counts)))
    
    # Calculate the confidence interval
    lower_bound = search_mean - margin_of_error
    upper_bound = search_mean + margin_of_error
    
    # Find the topic(s) with the highest search count within the confidence interval
    new_topics = []
    for t in data:
        if t[1] >= lower_bound and t[1] <= upper_bound:
            new_topics.append(t[0])
    
    return new_topics

def create_profile(apps, websites, texts):
    apps = [(app[1], app[2]) for app in apps]
    texts = [(text[1], text[2]) for text in texts]
    websites = [web[2] for web in websites]
    websites = [(t, websites.count(t)) for t in set(websites)]

    a_data = get_profile_data(apps)
    w_data = get_profile_data(websites)
    t_data = get_profile_data(texts)

    print(f"Most used app(s): {a_data}")
    print(f"Most researched topic(s): {w_data}")
    print(f"Most typed text(s): {t_data}")


def detect_anomaly(all_data, topic):

    topics = []
    for data in all_data:
        for i in range(data[2]):
            topics.append(data[1])

    # Filter the list of topics to only include those not related to the given topic
    non_topic_related = [x for x in topics if x != topic]
    
    # Set the confidence level
    confidence_level = 0.95
    
    # Calculate the sample proportion of the non-topic related topics
    sample_proportion = len(non_topic_related) / len(topics)
    
    # Calculate the standard error of the sample proportion
    standard_error = np.sqrt((sample_proportion * (1 - sample_proportion)) / len(topics))
    
    # Calculate the t-value for the confidence interval
    degrees_of_freedom = len(topics) - 1
    t_value = t.ppf((1 + confidence_level) / 2, degrees_of_freedom)
    
    # Calculate the margin of error
    margin_of_error = t_value * standard_error
    
    # Calculate the lower and upper bounds of the confidence interval
    lower_bound = sample_proportion - margin_of_error
    upper_bound = sample_proportion + margin_of_error
    
    # Calculate the proportion of the topic-related topics
    topic_proportion = len([x for x in topics if x == topic]) / len(topics)
    
    # Check if the topic proportion falls outside of the confidence interval
    if topic_proportion < lower_bound or topic_proportion > upper_bound:
        print('anomaly')
        return True
    else:
        print('Okay')
        return False

# detect_anomaly(all_data, "BUSINESS")