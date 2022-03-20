#
# chat_ai.py
#
# Transformers powered Natural Language Processing introductory
# project. Utilize the Persona-Chat dataset to fine tune a ConvAIModel,
# with a base pretrained model weights provided by Hugging Face. 
#
# Designed to be utilized alongside KotakeeOS speech_server to allow
# users to "chat" with Kotakee. The contents of the "persona" of the
# user may be modified by changing the minimal_train.json file.
#
# Additional enhancements TODO:
#  - Automatically add to the minimal_train.json file while
#    conversing - online model. 
#  - Generate more entries in the dataset to better fine-tune
#    the model. 
#  - Improve model performance. 
#
# Simple Transformers ConvAIModel docs:
# https://simpletransformers.ai/docs/convAI-model/ 
#
# Project concept guidance:
# https://towardsdatascience.com/how-to-train-your-chatbot-with-simple-transformers-da25160859f4

from simpletransformers.conv_ai import ConvAIModel
import time

class ChatAi:
  # Remember that all paths are relative to the wrapper class
  # module_active.py. 
  dependencies_location = "./chat_ai/chat_ai_dependencies"
  model_location = "./chat_ai/chat_ai_dependencies/gpt_personachat_cache"
  # Files expected to be within the dependencies folder.
  minimal_train_name = "minimal_train.json"

  model = None
  model_use_cuda = False # Change if you're training the model. 

  # Initialization occurs alongside chat_ai_parsing active module and
  # stays in place until the timeout is exhausted. Keep models 
  # loaded until then.
  def __init__(self):
    print("[DEBUG] Initializing ChatAI...")
    start_time = time.time()

    # Create a ConvAIModel, loading the pretrained weights from 
    # the specified location. 
    self.model = ConvAIModel("gpt", self.model_location, use_cuda=self.model_use_cuda)

    end_time = time.time()
    print("[DEBUG] ChatAI successfully initialized in " + str(end_time-start_time) + " seconds.")

  # Active model usage routine. Allows for interactions. Expects
  # a new message from the user and returns the model's predicted
  # response, as well as the aggregated history. If continuing
  # an existing conversation, the conversation_history should
  # also be provided. A personality may also be provided - if
  # not, a random persona will be assumed. 
  def model_interact(self, new_message, conversation_history = [], personality = None):
    print("[DEBUG] ChatAI recieved new message '" + new_message + "'. Processing...")
    start_time = time.time()
    ai_response, conversation_history = self.model.interact_single(
      message=new_message, history=conversation_history, personality=personality)
    end_time = time.time()
    print("[DEBUG] ChatAI responded with message '" + ai_response + "' in " + str(end_time-start_time) + " seconds.")
    return ai_response, conversation_history

  # Further train the model on the the minimal_train json file -
  # primarily intended to tweak the pretrained model. 
  def fine_tune_model(self):
    train_dataset_location = self.dependencies_location + "/" + self.minimal_train_name
    print("[DEBUG] Fine-tuning ChatAI with train json file located at: " + train_dataset_location)
    self.model.train_model(train_dataset_location)

  # Trains a fresh model on the default Persona dataset. If
  # the datset is missing, it will be downloaded automatically.
  def train_model_persona(self):
    self.model.train_model()

  # Evaluates a model on the default Persona datset. If the
  # dataset is missing, it will be downloaded automatically. 
  def evaluate_model_persona(self):
    self.model.eval_model()