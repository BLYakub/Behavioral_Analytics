import sqlite3
import numpy as np
from scipy.stats import t, norm, beta
from scipy.optimize import minimize_scalar

conn = sqlite3.connect('my_db.db')
c = conn.cursor()

def get_profile_data(data):
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


def detect_anomaly(topics, topic):

    # Filter the list of topics to only include those not related to the given topic
    non_topic_related = [x for x in topics if x != topic]
    
    # Set the confidence level
    confidence_level = 0.9
    
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
    

def bayes_detect_anomaly(topic_data, topic, alpha_val=1, beta_val=1):
    """
    Detects if the topic is an anomaly according to the given list of topic data using
    Bayesian statistics. Calculates the probability of a type 1 error (false positive)
    and the probability of a type 2 error (false negative), and uses the probabilities
    as a threshold to determine whether the given topic is an anomaly.

    Args:
        topic (str): The topic to check for anomalies.
        topic_data (list): A list of topic data to use for comparison.
        alpha (float): The alpha parameter of the prior Beta distribution. Default is 1.
        beta (float): The beta parameter of the prior Beta distribution. Default is 1.

    Returns:
        anomaly (bool): True if the topic is an anomaly, False otherwise.
    """

    # Get alpha and beta values
    alpha_val, beta_val = estimate_parameters(topic_data)

    # alpha_val = 3.905739766087065
    # beta_val = 6.320753443739576

    # Calculate the posterior distribution of the topic
    n = len(topic_data)
    k = topic_data.count(topic)
    posterior_alpha = alpha_val + k
    posterior_beta = beta_val + n - k
    posterior = beta(posterior_alpha, posterior_beta)

    # Calculate the probability of a type 1 error (false positive)
    false_positive = posterior.cdf(0.05)

    # Calculate the probability of a type 2 error (false negative)
    false_negative = 1 - posterior.cdf(0.95)

    # Use the probabilities as a threshold to determine whether the given topic is an anomaly
    if false_positive < 0.05 and false_negative < 0.05:
        print("okay")
        return False
    
    print("anomaly")
    return True


def estimate_parameters(data):

    values = [data.count(i) for i in set(data)]
    scaled_data = [(value - min(values)) / (max(values) - min(values)) for value in values]
    scaled_data = np.clip(scaled_data, 0.01, 0.99)    
    alpha_val, beta_val, loc, scale = beta.fit(scaled_data, floc=0, fscale=1)
    return alpha_val, beta_val


# c.execute("SELECT * FROM texts WHERE user_id = 'user_1'")
# texts = c.fetchall() 
# texts_data = []
# for data in texts:
#     for i in range(data[2]):
#         texts_data.append(data[1])

# c.execute("SELECT * FROM websites WHERE user_id = 'user_1'")
# websites = c.fetchall()

# c.execute("SELECT * FROM apps WHERE user_id = 'user_1'")
# apps = c.fetchall()

# create_profile(apps, websites, texts)

# print(texts_data)

# print(estimate_parameters(texts_data))
# print(bayes_detect_anomaly(texts_data, "HEALTH"))
# print(detect_anomaly(texts_data, "SCIENCE"))