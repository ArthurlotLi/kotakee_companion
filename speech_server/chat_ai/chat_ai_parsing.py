#
# chat_ai_parsing.py
#
# Handles user interactions with the chat_ai class - active module
# utilized by interaction_active. 

from chat_ai import ChatAi

import json

class ChatAiParsing:
  speech_speak = None
  speech_listen = None

  user_cancel_words = ["stop", "cancel", "no", "wrong", "end", "terminate", "freeze all motor functions"] 

  chat_ai = None

  # Some fun preset personas. Allow users to select from them
  # when starting up the chat. Loaded from the preset_personas.json
  # file. 
  preset_personas = None
  perset_personas_location = "./chat_ai/preset_personas.json"

  def __init__(self, speech_speak, speech_listen):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen

    # Load the preset personas file. Don't bother with error
    # parsing because active modules will handle the catching. 
    json_file = open(self.perset_personas_location)
    self.preset_personas = json.load(json_file)

    # Initialize ChatAI.
    self.chat_ai = ChatAi()

  # Level 1 standard routine. 
  def parse_command(self, command):
    valid_command = False

    if("chat" in command or "chatbot" in command or "talk" in command):
      valid_command = True
      # Allow users to provide personas. If no persona is provided, 
      # a ransom one will be selected from the PersonaChat dataset. 
      personality_name = None

      for word in command.split():
        if personality_name is None and word in self.preset_personas:
          # The name of a persona was provided. Use it directly.
          personality_name = word

      if personality_name is None:
        # List all personas for user and ask them to specify one.
        persona_prompt = "Please choose from the following personas: "
        for persona in self.preset_personas:
          persona_prompt = persona_prompt + persona + ", "
        user_response = self.speech_listen.listen_response(prompt=persona_prompt, execute_chime = True)

        if user_response is not None:
          for word in user_response.split():
            if personality_name is None and word in self.preset_personas:
              # The name of a persona was provided. Use it directly.
              personality_name = word

      # If personality_name is none, we can't proceed.
      if personality_name is not None:
        init_chatbot_prompt = "Starting ChatAI with persona '" + personality_name + "'. What would you like to say?"
        personality = self.preset_personas[personality_name]

        user_response = self.speech_listen.listen_response(prompt=init_chatbot_prompt, execute_chime = True)

        if user_response is not None:
          self.conversation_routine(message=user_response, personality=personality)

    return valid_command

  # Conversation loop. Takes in optional first message as well as a
  # personality strings list. 
  def conversation_routine(self, message, personality):
    print("[DEBUG] ChatAI conversation routine started.")
    end_conversation = False
    conversation_history = []

    while end_conversation is False:
      if message is None or any (x in message.split() for x in self.user_cancel_words):
        end_conversation = True
      else:
        # Continue the conversation. 
        ai_response, conversation_history = self.chat_ai.model_interact(message, conversation_history, personality=personality)
        # Allow user to respond to ai response. 
        message = self.speech_listen.listen_response(prompt=ai_response, execute_chime = True)

    self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Stopping ChatAI.")
    print("[DEBUG] ChatAI conversation routine completed.")