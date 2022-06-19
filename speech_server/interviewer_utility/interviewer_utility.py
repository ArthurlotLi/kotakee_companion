#
# interviewer_utility.py
#
# Provides interviewer capabiltiy given endgame_preparation contents.
# Don't stop improving! 

import sys
from random import sample
from pathlib import Path

_generator_folder = "../../endgame_preparation/question_generator"
_generator_questions = "../../endgame_preparation/questions"
_generator_class = "GenerateQuestion"

_interview_categories = ["mle_theory"] # TODO: "behavioral", "mle_system_design", "statistics", "linear algebra", "counting", ...

class InterviewerUtility:
  answered_questions = []

  def __init__(self, speech_speak):
    self.speech_speak = speech_speak

    # Load the inference class. 
    print("[DEBUG] InterviewerUtility - Importing generator class.")
    self._generator_class = self._load_class(module_name=_generator_folder, 
                                            class_name=_generator_class)
    if self._generator_class is None:
      print("[ERROR] InterviewerUtility - Failed to import generator class!")
      return
    
    # Initialize the inference class. Load the model immediately. 
    self._generator = self._generator_class()
    print("[DEBUG] InterviewerUtility - Load successful.")

  def parse_command(self, command):
    """
    Level 1 standard routine. Return True if the command applies.
    """
    
    if(self._generator is not None and ("interview" in command or "question" in command)):
      if("new" in command or len(self.answered_questions) == 0): 
        self.answered_questions = []
        output = "It's nice to meet you Arthur thank you for coming today. Welcome to your new interview. My name is " + self.speech_speak.multispeaker_synthesis_speaker + " and I will be your interviewer today. Let's begin."
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=output) 
      self.output_question(category = sample(_interview_categories, 1)[0])
    else:
      return False
    
    return True

  def output_question(self, category):
    if self._generator is not None:
      question =  self._generator.generate_question(category, questions_to_skip=self.answered_questions, 
                                                    questions_folder = Path(_generator_questions))
      question_text = "Question %d: %s" % (len(self.answered_questions) + 1, question)
      self.answered_questions.append(question)

      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=question_text) 

  def _load_class(self,  module_name, class_name):
    """
    Dynamic class import. Changes sys.path to navigate directories
    if necessary. Utilized for emotion detection and
    representation classes. 
   
    Expects module_name Ex) ./home_automation/home_automation
    and class_name Ex) HomeAutomation
    """
    module = None
    imported_class = None
    module_file_name = None

    sys_path_appended = False

    # Ex) ./home_automation - split by last slash. 
    # Don't bother if the original file is not within a subdirectory.
    split_module_name = module_name.rsplit("/", 1)
    module_folder_path = split_module_name[0]
    if(module_folder_path != "." and len(split_module_name) > 1):
      sys.path.append(module_folder_path)
      module_file_name = split_module_name[1]
      sys_path_appended = True
    else:
      module_file_name = module_name.replace("./", "")

    # Fetch the module first.
    try:
      module = __import__(module_file_name)
    except Exception as e:
      print("[ERROR] Failed to import module " + module_file_name + " from subdirectory '" + module_folder_path + "'.")
      print(e)
      return None
      
    # Return the class. 
    try:
      imported_class = getattr(module, class_name)
    except Exception as e:
      print("[ERROR] Failed to import class_name " + class_name + ".")
      print(e)
      return None

    if sys_path_appended is True:
      sys.path.remove(module_folder_path)

    return imported_class