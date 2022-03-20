#
# emotion_detection_utility.py
#
# "Production" utilization of generated emotion detection models.
# Utilizes models saved in the local "model" folder to predict
# an emotion category given an input text. 
#
# This implementation is based upon the Paul Ekman Discrete Emotion
# Model (DEM) of human emotion with 6 categories, alongside an
# additional "neutral" category. Together, the 7 possible solutions
# for the model are:
#  0 Joy
#  1 Sadness
#  2 Fear
#  3 Anger
#  4 Disgust
#  5 Surprise
#  6 Neutral
#
# Expects models to have been placed in ../emotion_detection/models,
# relative to the speech_server.py location.

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class EmotionDetectionUtility:
  # Default is based off the speech_server level. May be 
  # overridden during initialization.
  model_variants_location = "../../emotion_detection/models"

  model = None
  tokenizer = None
  device = None

  # Mapping integers to their solutions. Should be synchronized with
  # solution_string_map class variables found in supporting classes.
  solution_int_map = ["joy", "sadness", "fear", "anger", "disgust", "surprise", "neutral"]

  # Maximum input for the model is 256 by default(see emotion 
  # detection harness class variable). However, in the interest
  # of speed, you may specify a lower number than this to truncate
  # incoming text. 
  #
  # Specified to 125 as longer sentences take 3.3 seconds on the 
  # crappy macbook and don't result in necessarily better predicitons.
  max_seq_length = 125
    
  # Upon initialization, attempt to load the model specified.
  # Allow user to provide model location and override the default.
  def __init__(self, model_num, use_cpu = True, model_variants_location = None):
    print("[DEBUG] Initializing EmotionDetectionUtility with model number "+str(model_num)+"...")

    # Override the default location if provided. This is because
    # the default is based off the speech_server level. 
    if model_variants_location is not None:
      self.model_variants_location = model_variants_location

    model, tokenizer, device = self.load_tokenizer_and_model(model_num=model_num, device=None, use_cpu=use_cpu)

    if model is None or tokenizer is None or device is None:
      print("[ERROR] Failed to load model, tokenizer, or device properly. Initialization failed.")
    else:
      self.model = model
      self.tokenizer = tokenizer
      self.device = device
      print("[DEBUG] EmotionDetectionUtility initialized successfully.")

  # Given a model_num, return the tokenizer and model stored at the
  # expected location. Loads the device to run it on if it is not 
  # provided. Also returns the device in case it is needed.
  def load_tokenizer_and_model(self, model_num, device = None, use_cpu = False):
    # Grab the device first if we don't have it. 
    if device is None:
      device = self.train_model_load_device(use_cpu = use_cpu)

    try:
      model_path = self.model_variants_location + "/" + str(model_num)
      print("[DEBUG] Loading Tokenizer for model " + str(model_num) + " from '" + model_path + "'.")
      tokenizer = AutoTokenizer.from_pretrained(model_path)
      print("[DEBUG] Loading Model for model " + str(model_num) + " from '" + model_path + "'.")
      model = AutoModelForSequenceClassification.from_pretrained(model_path)

      print("[DEBUG] Loading Model onto device.")
      model.to(device)

      return model, tokenizer, device
    except Exception as e:
      print("[ERROR] Unable to load model " + str(model_num) + ". Exception: ")
      print(e)
    return None, None, None

  # Load the device for torch work. Expects a boolean indicating whether
  # we'll be using the CPU. Returns None in the event of a GPU CUDA load
  # failure.
  def train_model_load_device(self, use_cpu):
    device = None

    if not use_cpu:
      # Note we expect to be using CUDA for this training session. If we
      # encounter an error, we'll just stop. 
      try:
        print("[DEBUG] Verifying CUDA: ", end="")
        print(torch.zeros(1).cuda())
        print("[DEBUG] CUDA version: ", end="")
        print(torch.version.cuda)
        print("[DEBUG] Torch CUDA is available: " + str(torch.cuda.is_available()))
      except:
        print("[ERROR] Unable to access Torch CUDA - was pytorch installed from pytorch.org with the correct version?")
        return None
      
      device = torch.device("cuda") 
      print("[DEBUG] GPU with CUDA successfully added as device.")
    else:
      device = torch.device("cpu") # Use the CPU for better debugging messages. 
      print("[DEBUG] CPU successfully added as device.")
    
    return device

  # Execute predictions given a string. Returns the solution string
  # itself (Ex) "joy")
  def predict_emotion(self, text):
    # In case of a failed initialization, just use neutral.
    if self.model is None or self.tokenizer is None or self.device is None:
      print("[WARNING] EmotionDetectionUtility failed initialization - defaulting to neutral emotion.")
      return "neutral"

    # TODO: Remove stop words?

    print("[INFO] EmotionDetectionUtility processing given text of length "+str(len(text))+"...")

    # Encode the text with the tokenizer we loaded.
    encoded_text = self.tokenizer.encode_plus(
      text, 
      return_tensors="pt", 
      max_length = self.max_seq_length, 
      truncation=True)
    
    # Send the text to the device.
    sequence = encoded_text["input_ids"].to(self.device)

    # Make predictions with the model we loaded.
    outputs = self.model(sequence)

    # The output of the predictions contains a vector of logits that 
    # output unnormalized log probabilities likened to confidence
    # values.
    logits = outputs[0]

    # The logits will output a vector listing confidence of all
    # of the classes it considered even remotely likely.
    # Ex) [-0.14414964616298676, -0.06529509276151657, -0.49382615089416504, 2.442490339279175, 1.221635341644287, -0.23346763849258423, -1.888406753540039]
    #
    # We want to normalize the probabilities. We can do this using
    # the softmax that will normalize the log probabilities that were
    # output by the model. (Softmax: The sigmoid in n dimensional 
    # space)
    probability_vector = torch.softmax(logits, dim=1).detach().cpu().tolist()[0]

    # Parse the vector and grab the 3rd highest confidence 
    # options. (Kinda messy, but as far as I believe this is
    # fastest way)
    max_prediction_index = None
    max_prediction_confidence = -999
    second_max_prediction_index = None
    second_max_prediction_confidence = None
    third_max_prediction_index = None
    third_max_prediction_confidence = None
    for i in range(0, len(probability_vector)):
      prediction = probability_vector[i]
      if prediction > max_prediction_confidence:
        # Shuffle the three. 
        third_max_prediction_index = second_max_prediction_index
        third_max_prediction_confidence = second_max_prediction_confidence
        second_max_prediction_index = max_prediction_index
        second_max_prediction_confidence = max_prediction_confidence
        # Convert all probabilities into percentages. 
        max_prediction_index = i
        max_prediction_confidence = prediction*100

    max_prediction = None
    second_max_prediction = None
    third_max_prediction = None

    if max_prediction_index is not None:
      max_prediction = self.solution_int_map[max_prediction_index]
    if second_max_prediction_index is not None:
      second_max_prediction = self.solution_int_map[second_max_prediction_index]
    if third_max_prediction_index is not None:
      third_max_prediction = self.solution_int_map[third_max_prediction_index]

    # Output the results for debug and return the maximum
    # confidence. 
    print("[INFO] Best Prediction: " + str(max_prediction) + " ("+str(max_prediction_confidence)+")")
    print("                   2nd: " + str(second_max_prediction) + " ("+str(second_max_prediction_confidence)+")")
    print("                   3nd: " + str(third_max_prediction) + " ("+str(third_max_prediction_confidence)+")")

    return max_prediction

# For debug purposes only, test a simple text for emotion category. 
if __name__ == "__main__":
  model_num = 2
  text = "I hate you!"
  model_variants_location = "./models"

  emotion_detection = EmotionDetectionUtility(model_num=model_num, model_variants_location = model_variants_location)
  emotion_detection.predict_emotion(text = text)