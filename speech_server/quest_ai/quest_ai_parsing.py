#
# quest_ai_parsing.py
#
# Provides speech interfacing capability with QuestAI, abstracting
# functionality from commandParsing. Interacts with user who has
# activated QuestAI, prompting for a question, receiving the 
# questions, and providing a response.
#
# A potential enhancement to this class is a follow-up prompt
# asking for the success/failure of the prediction (if applicable
# to the question).

from quest_ai import QuestAi

class QuestAiParsing:
  # Dictates whether we use Google or Pocket Sphinx (former is online)
  online_functionality = True 

  level_2_prompt = "What would you like to know?"
  level_2_confirmation = "Let's see..."
  cancelWords = ["stop", "nevermind", "never mind", "cancel"] # input string should be exactly these. 

  speech_speak = None
  speech_listen = None
  web_server_status = None
  questAi = None

  def __init__(self, speech_speak, speech_listen, web_server_status):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status 

    # Initialize QuestAI. 
    self.questAi = QuestAi()

  # Level 1 standard routine. 
  def parse_command(self, command):
    valid_command = False

    if("question" in command):
      # If we asked for advanced output or "8 ball", our output should be
      # different.
      output_type = 0
      if("advanced" in command or "detailed" in command): output_type = 1
      elif("eight ball" in command or "8-ball" in command or "8 ball" in command): output_type = 2
      self.standard_query(output_type = output_type, online_functionality=self.web_server_status.action_states is not None)
      valid_command = True
    
    return valid_command

  # Level 2 command parsing. A user has activated 
  # QuestAI, and we handle further interactions here. 
  #
  # Various output types depending on user specification.
  #   0 - Yes or no response.
  #   1 - Advanced response.
  #   2 - 8 Ball response. 
  def standard_query(self, output_type = 0, online_functionality = True):
    print("[DEBUG] Initializing QuestAI Standard Query procedure.")
    self.online_functionality = online_functionality
    user_response = self.speech_listen.listen_response(prompt=self.level_2_prompt, execute_chime = False)

    if user_response is None:
      print("[DEBUG] No response recieved. Stopping QuestAI...")
      return

    if user_response in self.cancelWords:
      print("[DEBUG] User requested cancellation. Stopping QuestAI...")
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Stopping Quest AI...")
      return

    # We now have a question. Pass it to the model class - we
    # expect a boolean back + confidence. 
    self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=self.level_2_confirmation) # Because the response will likely take some time. 
    ai_response, ai_yes_amount, ai_confidence, ai_source, ai_8_ball = self.questAi.generate_response(user_response)
    print("[DEBUG] QuestAI Standard Query returned response: " + str(ai_response) + ".")

    # Handle the response to the user. 
    # 0 = Standard response.
    if(output_type == 0):
      response_text = ""
      if ai_response is True:
        response_text = "I believe so."
      else:
        response_text = "I don't think so."
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=response_text)

    # 1 = Advanced response. 
    elif(output_type == 1):
      response_text = ""
      if ai_response is True:
        response_text = "I believe so, with " + str(round(ai_yes_amount*100, 2)) + " percent certainty."
      else:
        response_text = "I don't think so, with " + str(round((1-ai_yes_amount)*100, 2)) + " percent certainty."

      response_text = response_text + " I am " + str(round(ai_confidence*100, 2)) + " percent confident. My source: " + str(ai_source) + "."
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=response_text)

    # 2 = Magic 8 ball response. 
    else:
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=ai_8_ball)
    
    # TODO In the future, we should add a mechanism to prompt for 
    # whether we did good in that prediction (so we can append 
    # the transcript to a SQL database or something as a new data point)