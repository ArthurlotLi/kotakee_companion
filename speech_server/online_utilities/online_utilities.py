#
# online_utilites.py
#
# Provides an assortment of functions to allow the user to interact
# with open internet resources. 

class OnlineUtilities:
  wikipedia_query_max_sentences = None # Configurable. If not specified, will not pass argument. 
  news_api_key = "a7287b5b00a641e7b532a75007226944" # TODO: Leave this here for now. 
  news_api_url = " https://newsapi.org/v2/top-headlines"
  news_api_possible_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
  news_api_results = 15 # Default is 20, 100 is maximum.

  def __init__(self, speech_speak):
    self.speech_speak = speech_speak

  def parse_command(self, command):
    """
    Level 1 standard routine. Return True if the command applies.
    """

    # Given keywords, attempt to grab a summary from the wikipedia
    # API. 
    if("wikipedia" in command or "summary" in command or "summarize" in command):
      self.query_wikipedia(command)
    elif("news" in command or "headlines" in command):
      self.query_news(command)
    else:
      return False

    return True
  
  def query_wikipedia(self, command):
    """
    Grabs the top-level summary using the wikipedia API. Note that the
    search function isn't... the greatest. 
    """
    wikipedia_query = command.replace("wikipedia", "")
    wikipedia_query = wikipedia_query.replace("summary", "")
    wikipedia_query = wikipedia_query.replace("summarize", "")
    wikipedia_query = wikipedia_query.strip()

    import wikipedia
    print("[DEBUG] Attempting to query wikipedia summary for keywords: '" + str(wikipedia_query) + "'.")
    wiki_passage = ""
    try:
      # Don't pass the sentences requirement because in doing so
      # you'll get more than you bargained for. 
      summary = None
      if self.wikipedia_query_max_sentences is None:
        summary = wikipedia.summary(wikipedia_query)
      else:
        summary = wikipedia.summary(wikipedia_query, sentences = self.wikipedia_query_max_sentences)
      wiki_passage += summary.strip() + " "
    except:
      pass

    response_to_query = ""
    
    if len(wiki_passage) > 0:
      response_to_query = wiki_passage
    else:
      response_to_query = "Sorry, I was unable to find a matching wikipedia page using the keywords: '" + str(wikipedia_query) + "'."
    
    self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=response_to_query) 


  def query_news(self, command):
    """
    Allows user to request information from the Web API 2.0. Will
    by default request the highest headlines. Allows user to specify
    category or keywords. 
    """
    import requests

    query_params = {
      "apiKey" : self.news_api_key,
      "pageSize" : self.news_api_results
    }

    # Allows for keyword parsing. 
    if "keyword" in command or "keywords" in command:
      if "keyword" in command: keyword_or_phrase = command.split("keyword", 1)[1].strip()
      else: keyword_or_phrase = command.split("keywords", 1)[1].strip()
      query_params["q"] = keyword_or_phrase
      print("[DEBUG] Online Utilities - Executing news API call with keyword(s) \"%s\"." % keyword_or_phrase)
      response_to_query = "Here are the articles I found after searching for, %s." % keyword_or_phrase

    # Alternatively, apply one and only one category.
    elif any(x in command for x in self.news_api_possible_categories):
      for category in self.news_api_possible_categories:
        if category in command:
          query_params["category"] = category
          query_params["country"] = "us"
          print("[DEBUG] Online Utilities - Executing news API call with category of %s." % category)
          response_to_query = "Here are the articles I found for %s." % category
          break
      assert "category" in query_params # Sanity check.

    # Otherwise, just query for headlines.
    else:
      print("[DEBUG] Online Utilites - Executing news API call for unfiltered top headlines.")
      query_params["category"] = "general"
      query_params["country"] = "us"
      response_to_query = "Here are today's headlines."
    
    # We have our formulated query. Execute it. 
    try:
      api_result = requests.get(self.news_api_url, params = query_params)
      api_result_json = api_result.json()
      articles = api_result_json["articles"]

      if len(articles) == 0:
        response_to_query = "I'm sorry, I was unable to find any articles for you."
      else:
        for article in articles:
          split_article_title = article["title"].rsplit(" - ", 1)
          headline, article_source = split_article_title[0], split_article_title[1]
          response_to_query += " " + article_source + ", " + headline
      
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=response_to_query) 

    except Exception as e:
      print("[ERROR] Online Utilites - Failed to execute or parse API call. Exception:")
      print(e)
  