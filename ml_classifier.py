from sklearn.svm import SVC
import spacy_sentence_bert
import pandas as pd
from sklearn.model_selection import train_test_split
import sqlite3
import pickle

conn = sqlite3.connect('my_db.db')
c = conn.cursor()


# load the model from disk
loaded_model = pickle.load(open('web_title_model.sav', 'rb'))

# fake_model = pickle.load(open('fake_model.sav', 'rb'))

nlp = spacy_sentence_bert.load_model('en_stsb_distilbert_base')


# Train the machine learning model
def train_model():
  global loaded_model

  c.execute("SELECT text, subject FROM label_data WHERE verified = '1'")
  web_data = c.fetchall()
  data = []

  for line in web_data:
    dic = {"title": line[0], "topic": line[1]}
    data.append(dic)

  df = pd.DataFrame(data)

  # print(df.head())
  topics = df.topic.unique()

  for topic in topics:
    temp_df = df[df['topic'] == topic][:5000]
    df = pd.concat([df, temp_df])

  df['vector'] = df['title'].apply(lambda x: nlp(x).vector)

  X_train, X_test, y_train, y_test = train_test_split(df['vector'].tolist(), df['topic'].tolist(), test_size=0.33, random_state=42)

  clf = SVC(gamma='auto')
  clf.fit(X_train, y_train)

  loaded_model = clf

  # save model 
  filename = 'web_title_model.sav'
  pickle.dump(clf, open(filename, 'wb'))



def train_fake_model():
  # global fake_model
  global loaded_model

  print("Begin Training")
  c.execute("SELECT text, subject FROM label_data WHERE verified = '1'")
  web_data = c.fetchall()
  data = []
  
  for line in web_data:
    dic = {"title": line[0], "topic": line[1]}
    data.append(dic)

  df = pd.DataFrame(data)

  # print(df.head())
  topics = df.topic.unique()

  for topic in topics:
    temp_df = df[df['topic'] == topic][:5000]
    df = pd.concat([df, temp_df])

  df['vector'] = df['title'].apply(lambda x: nlp(x).vector)

  X_train, X_test, y_train, y_test = train_test_split(df['vector'].tolist(), df['topic'].tolist(), test_size=0.33, random_state=42)

  clf = SVC(gamma='auto')
  clf.fit(X_train, y_train)

  # fake_model = clf
  loaded_model = clf

  filename = 'fake_model.sav'
  pickle.dump(clf, open(filename, 'wb'))
  print("finish training")


# Practice prediction accuracy of the model
def practice_predict(model):
  headlines = ["Scientists Figured Out How Much Exercise You Need to 'Offset' a Day of Sitting",
  "FC Barcelona wins UCL for the 10th time due to Messi's comeback from injury",
  "Increasing mental health issues a symptom of Victoria's lockdown",
  'Philippines polio outbreak over: UN',
  "Sophie, Countess of Wessex opens up about menopause: 'It's like somebody's just gone and taken your brain'",
  'Bill Gates tells why he prefers Android mobile over iPhone',
  "'A weight has been lifted' Edinburgh pubs and restaurants react to hospitality rules easing",
  "Mysterious Signal Flashing From Galaxy's Core Baffle Scientists; Where Is There Source of This Radio Waves?",
  "'Tears in their eyes': World erupts over All Blacks' beautiful Maradona tribute",
  "Green Bay Packers lose super bowl!"]

  topics = ['SCIENCE',  'SPORTS',  'HEALTH',
  'HEALTH',  'ENTERTAINMENT',  'TECHNOLOGY',  'BUSINESS',
  'SCIENCE',  'ENTERTAINMENT',  'SPORTS']

  for headline, topic in zip(headlines, topics):
    print(headline)
    print(f"True Label: {topic}, Predicted Label: {model.predict(nlp(headline).vector.reshape(1, -1))[0]} \n")


# Predict topic of the given text using the model
def predict_topic(text):
  topic = loaded_model.predict(nlp(text).vector.reshape(1, -1))[0]
  # return topic
  return topic
