#
# machine_pianist_utility.py
#
# Allows for utilization of trained Machine Pianist models - models
# that "perform" a midi file, outputing a midi that has been
# augmented with human-like performace data, such as velocities
# and control changes (pedals). 
#
# Every time a song is played, create a unique performance using
# the machine pianist and a base MIDI file. Use the product midi
# file as necessary. 

import sys
import base64
from pathlib import Path

class MachinePianistUtility:
  _inference_class = None
  _inference = None

  def __init__(self, model_path: str, inference_folder: str, 
               inference_class: str):
    """
    Given the model to use as well as the details of the production
    inference, load the class (and thus the model).
    """
    print("[DEBUG] MachinePianistUtility - Loading model at %s." % model_path)
    self.model_path = model_path
    self.inference_folder = inference_folder
    self.inference_class = inference_class

    # Check the model actually exists. 
    if not Path(model_path).exists():
      print("[ERROR] MachinePianistUtility - Model does not exist at %s! Machine Pianist disabled." % model_path)
      return
    
    # Load the inference class. 
    print("[DEBUG] MachinePianistUtility - Importing inference class.")
    self._inference_class = self._load_class(module_name=inference_folder, 
                                            class_name=inference_class)
    if self._inference_class is None:
      print("[ERROR] MachinePianistUtility - Failed to import inference class!")
      return
    
    # Initialize the inference class. Load the model immediately. 
    self._inference = self._inference_class(model_path= Path(model_path))
    print("[DEBUG] MachinePianistUtility - Load successful.")

  def perform_midi(self, midi_file: Path, temp_file: Path):
    """
    Given a list of a single midi location, have the model infer
    performance data and augment the file. Save the file to a temp
    file and return the filename.  

    Returns None or the name of the temp file that was saved. 
    """
    if self._inference is None: return None

    print("[INFO] MachinePianistUtility - Submitting song to be performed to model.")
    # We get a list of mido MidiFiles back. 
    midis = self._inference.perform_midis(midi_files = [str(midi_file)])

    # Write the mido file to the temp file. 
    midis[0].save(str(temp_file))

    return str(temp_file)
  

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