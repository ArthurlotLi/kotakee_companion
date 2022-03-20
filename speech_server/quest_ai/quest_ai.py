#
# quest_ai
#
# RoBERTa-powered Natural Language Processing introductory project. 
# Given a yes/no question, use various internet sources for context
# before using RoBERTa to derive a boolean response. 
#
# Designed to be utilized alongside KotakeeOS speechServer to allow
# users to ask their home assistant yes/no questions in conjunction
# with the Trigger Word Detection machine learning solution. Should
# be a pretty fun little project to introduce me to NLP. 
#
# Additonal enhancements TODO:
#  - Learn to tune the RoBERTa model yourself
#  - Implement automated dataset additions/separate personal dataset
#    source
#
# Base code from here:
# https://towardsdatascience.com/building-an-ai-8-ball-with-roberta-2bfbf6f5519b 
#

import random
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import tensorflow as tf
import tensorflow_hub as hub
from codecs import decode
import math
import pickle
import jsonlines
from scipy import spatial
import spacy.cli
import spacy
import pickle

import time

class QuestAi:

  # Path should expect to run from the speech_server directory. 
  dependencies_location = "./quest_ai/quest_ai_dependencies/"

  nlp = None
  answers = None
  tokenizer = None
  model = None
  question_tree = None
  encoding_model = None
  boolq_data = None

  def __init__(self):
    print("[DEBUG] Initializing QuestAI...")
    start_time = time.time()

    encoding_module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/5"
    self.encoding_model = hub.load(encoding_module_url)
    self.device = torch.device("cpu") # USE CPU ONLY - if it's on the GPU we run out of VRAM. No need for it to be fast. 
    # Set seeds for reproducibility
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    model_path = self.dependencies_location + "roberta-large_fine-tuned"
    print("Loading tokenizer from " + model_path)
    self.tokenizer = AutoTokenizer.from_pretrained(model_path)
    print("Loading model from " + model_path)
    self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
    _ = self.model.to(self.device)

    self.boolq_data = []
    for file_name in ["dev.jsonl", "test.jsonl", "train.jsonl"]:
      with jsonlines.open(self.dependencies_location + file_name) as file:
          for line in file.iter():
            self.boolq_data.append(line)

    encoded_qs = pickle.load(open(self.dependencies_location + "encoded_qs.pkl", "rb"))
    self.question_tree = spatial.KDTree(encoded_qs)

    self.nlp = spacy.load("en_core_web_sm")
    self.nlp.add_pipe("textrank")
    self.answers = pickle.load(open(self.dependencies_location + "answers.pkl", "rb"))

    end_time = time.time()
    print("[DEBUG] QuestAI successfully initialized in " + str(end_time-start_time) + " seconds.")

  def predict(self, question, passage):
    if len(question) == 0 or len(passage) == 0:
      return 0.5, 0.0
    sequence = self.tokenizer.encode_plus(question, passage, return_tensors="pt",
      max_length=512, truncation=True)['input_ids'].to(self.device)
    logits = self.model(sequence)[0]
    probabilities = torch.softmax(logits, dim=1).detach().cpu().tolist()[0]
    vector = logits.detach().cpu().tolist()[0]
    confidence = min(math.sqrt(vector[0]**2+vector[1]**2)/3.6, 1)
    proba_yes = probabilities[1]
    confidence = round(confidence, 3)
    return proba_yes, confidence

  def predict_and_print(self, question, passage):
    proba_yes, confidence = self.predict(question, passage)
    print(f"Question: {question}, Yes: {round(proba_yes,3)}, No: {round(1-proba_yes, 3)}, Confidence {confidence}")
    return proba_yes, confidence

  def embed(self, input):
    e = self.encoding_model([input])[0]
    proto_tensor = tf.make_tensor_proto(e)
    a = tf.make_ndarray(proto_tensor)
    return a.tolist()

  # For decoding the NYT API key. 
  def d(self, t): return decode(t,"base-64").decode()

  # Given a question, process an answer!
  def generate_response(self, question_text):
    print("[DEBUG] Attempting to generate response for the following text:\n'" + question_text + "'")

    query = ""
    keywords = self.nlp(question_text.lower())
    for p in keywords._.phrases[:5]:
      if p.rank > 0.01:
        query += p.text + " "
    query = query.strip()
    if len(query) == 0:
      query = question_text

    import wikipedia
    print("Checking the Wikipedia.")
    results = wikipedia.search(query, results = 3)
    wiki_passage = ""
    for r in results[1:]:
      try:
        s = wikipedia.summary(r)
      except:
        continue
      wiki_passage += s.strip() + " "
    wiki_passage = wiki_passage.replace("\n", " ")
    wiki_yes, wiki_conf = self.predict(question_text, wiki_passage)

    from pynytimes import NYTAPI
    nyt_passage = ""
    print("Checking the New York Times.")
    nyt = NYTAPI(self.d(b'R2xsdTF4S2lLMjdSc3dBOXZ0VkZwSjMxbmoyS1RjVzM=\n'))
    articles = nyt.article_search(query = query, results = 3,
      options = {"sort": "relevance"})
    for a in articles[:3]:
      nyt_passage += a["abstract"].strip() + " "
      nyt_passage += a["lead_paragraph"].strip() + " "
    nyt_yes, nyt_conf = self.predict(question_text, nyt_passage)

    boolq_passage = ""
    print("Checking the BoolQ Dataset.\n")
    question_embed = self.embed(question_text)
    result = self.question_tree.query(question_embed)
    if (result[0] < 1):
      index = result[1]
      boolq_passage = self.boolq_data[result[1]]["passage"]
      similar_question = self.boolq_data[result[1]]["question"]
    boolq_yes, boolq_conf = self.predict(question_text, boolq_passage)

    conf = 0
    yes = 0.5
    passage = ""
    source = "no source"

    if (wiki_conf > nyt_conf and wiki_conf > boolq_conf):
      yes = wiki_yes
      conf = wiki_conf
      passage = wiki_passage
      source = "Wikipedia"
    else:
      if (nyt_conf > boolq_conf):
        yes = nyt_yes
        conf = nyt_conf
        passage = nyt_passage
        source = "New York Times"
      else:
        yes = boolq_yes
        conf = boolq_conf
        passage = boolq_passage
        source = "BoolQ Dataset"

    import textwrap

    min_dist = float("inf")
    pick = 0
    answer_yes = False
    if yes > 0.5:
      answer_yes = True

    if (conf < 0.5):
      map_conf =  1 +  conf * 19 / 2
      for i, a in enumerate(self.answers[:5]):
        c = a[1][1]
        distance = abs(map_conf-c)
        if distance < min_dist:
          min_dist = distance
          pick = i
    else:
      map_yes = 1 + (yes * 1.5 if yes > 2/3 else yes) * 19 / 1.5
      for i, a in enumerate(self.answers[5:]):
        y = a[1][0]
        distance = abs(map_yes-y)
        if distance < min_dist:
          min_dist = distance
          pick = i+5

    print("The AI 8-Ball's Answer:", self.answers[pick][0], "\n")
    print("Yes:", str(round(yes*100, 2)) + "%")
    print("No:", str(round((1-yes)*100, 2)) + "%")
    print("Confidence:", str(round(conf*100, 2)) + "%")
    print("Source:", source)

    print(textwrap.fill("Passage: " + passage, width=150))

    return answer_yes, yes, conf, source, self.answers[pick][0]


if __name__ == "__main__":
  print("[DEBUG] Running QuestAI in debug!")

  test_question = "Can a computer beat a grandmaster chess player?" 

  questAi = QuestAi()
  questAi.generate_response(test_question)