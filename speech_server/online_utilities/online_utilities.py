#
# online_utilites.py
#
# Provides an assortment of functions to allow the user to interact
# with open internet resources. 

class OnlineUtilities:
  speech_speak = None

  wikipedia_query_max_sentences = None # If not specified, will not pass argument. 

  def __init__(self, speech_speak):
    self.speech_speak = speech_speak

  # Level 1 standard routine.
  def parse_command(self, command):
    valid_command = False

    # Given keywords, attempt to grab a summary from the wikipedia
    # API. 
    if("wikipedia" in command or "summary" in command or "summarize" in command):
      valid_command = True

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
        response_to_query = "I was unable to find a matching wikipedia page for the keywords: '" + str(wikipedia_query) + "'."
      
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=response_to_query) 

    return valid_command