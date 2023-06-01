import sqlite3
from scipy.stats import norm
import numpy as np
from collections import Counter
import math


conn = sqlite3.connect('my_db.db')
c = conn.cursor()


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


def create_profile(apps, websites, texts):

    apps = [(app[1], app[2]) for app in apps]
    texts = [(text[1], text[2]) for text in texts]
    websites = [web[2] for web in websites]
    websites = [(t, websites.count(t)) for t in set(websites)]

    a_data = get_profile_data(apps)
    w_data = get_profile_data(websites)
    t_data = get_profile_data(texts)

    # print(f"Most used app(s): {a_data}")
    # print(f"Most researched topic(s): {w_data}")
    # print(f"Most typed text(s): {t_data}\n")

    return a_data, w_data, t_data


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

# c.execute(f"SELECT * FROM texts WHERE user_id = 'user_1'")
# text_data = c.fetchall()
# topics = []
# for data in text_data:
#     for i in range(data[2]):
#         topics.append(data[1])

# print(is_anomaly("SCIENCE", topics))

# c.execute(f"SELECT * FROM apps WHERE user_id = 'user_1'")
# apps = c.fetchall()

# c.execute(f"SELECT * FROM websites WHERE user_id = 'user_1'")
# websites = c.fetchall()

# c.execute(f"SELECT * FROM texts WHERE user_id = 'user_1'")
# texts = c.fetchall()

# create_profile(apps, websites, texts)
# def conf_detect_anomaly(topic, topics):
#     # Filter the list of topics to only include those not related to the given topic
#     non_topic_related = [x for x in topics if x != topic]

#     # Set the confidence level
#     confidence_level = 0.9

#     # Calculate the proportion of the topic-related topics
#     topic_proportion = len([x for x in topics if x == topic]) / len(topics)

#     # Calculate the sample proportion of the non-topic related topics
#     sample_proportion = len(non_topic_related) / len(topics)

#     # Calculate the standard error of the sample proportion
#     standard_error = np.sqrt((sample_proportion * (1 - sample_proportion)) / len(topics))

#     # Calculate the t-value for the confidence interval
#     degrees_of_freedom = len(topics) - 1
#     t_value = t.ppf((1 + confidence_level) / 2, degrees_of_freedom)

#     # Calculate the margin of error
#     margin_of_error = t_value * standard_error

#     # Calculate the lower and upper bounds of the confidence interval
#     lower_bound = sample_proportion - margin_of_error
#     upper_bound = sample_proportion + margin_of_error

#     print(topic_proportion, upper_bound, lower_bound)
#     # Check if the topic proportion falls outside of the confidence interval
#     if topic_proportion < lower_bound or topic_proportion > upper_bound:
#         print('anomaly')
#         return True
#     else:
#         print('Okay')
#         return False