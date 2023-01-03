import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import sqlite3
import pickle

# conn = sqlite3.connect('my_db.db')
# c = conn.cursor()

# c.execute("SELECT title, topic FROM websites")
# web_data = c.fetchall()

# web_texts = []
# web_labels = []
# for data in web_data:
#     web_texts.append(data[0])
#     web_labels.append(data[1])

# # Load the dataset and labels
# texts = np.array(web_texts) # Replace this with your list of texts
# labels = np.array(web_labels) # Replace this with your list of labels

# # Preprocess the text data
# vectorizer = CountVectorizer()
# X = vectorizer.fit_transform(texts)

# # Split the dataset into training and testing sets
# X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.33, random_state=42)

# # Train a logistic regression model
# model = LogisticRegression()
# model.fit(X_train, y_train)

# Evaluate the model on the testing set
# accuracy = model.score(X_test, y_test)
# print("Accuracy: {:.2f}%".format(accuracy * 100))

# Save model in file
# filename = 'test_ml_model.sav'
# pickle.dump(model, open(filename, 'wb'))

model = pickle.load(open('web_title_model.sav', 'rb'))

# Classify a new, unseen text
vectorizer = CountVectorizer()
new_text = "Elon Musk creates new phone with unlimited battery"
new_text_vectorized = vectorizer.transform([new_text])
prediction = model.predict(new_text_vectorized)
print("Predicted label:", prediction)

# headlines = ["Gamestop stocks fall drastically cause massive dissruption in the stock trade",
# "FC Barcelona wins UCL for the 10th time due to Messi's comeback from injury",
# "Increasing mental health issues a symptom of Victoria's lockdown",
# 'Philippines polio outbreak over: UN',
# "'I'm terrified and praying to the acting gods' - Paul Mescal on star-studded first big screen role",
# 'Bill Gates tells why he prefers Android mobile over iPhone',
# "'A weight has been lifted' Edinburgh pubs and restaurants react to hospitality rules easing",
# "Mysterious Signal Flashing From Galaxy's Core Baffle Scientists; Where Is There Source of This Radio Waves?",
# "'Tears in their eyes': World erupts over All Blacks' beautiful Maradona tribute",
# "Green Bay Packers lose super bowl!"]

# topics = ['BUSINESS',  'SPORTS',  'HEALTH',
# 'HEALTH',  'ENTERTAINMENT',  'TECHNOLOGY',  'BUSINESS',
# 'SCIENCE',  'ENTERTAINMENT',  'SPORTS']

# for headline, topic in zip(headlines, topics):
#     new_text_vectorized = vectorizer.transform([headline])
#     prediction = model.predict(new_text_vectorized)
#     print(headline)
#     print(f"True Label: {topic}, Predicted Label: {model.predict(new_text_vectorized)} \n")
