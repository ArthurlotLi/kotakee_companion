#
# evaluate_model_spot_check.py
#
# Utilizes the class defined in evaluate_model.py to execute 
# spot-checking of multiple variants of the base model at once.

import argparse
import os
from evaluate_model import EvaluateModel

class SpotCheck:
  # Provide identifiers so you can see the results of training. 
  spot_check_results_location = "./spot_check_results"
  spot_check_results = []
  spot_check_dict = None

  def __init__(self, models_dict):
    self.spot_check_dict = models_dict

  # Given an interation number execute Evaluate Model multiple
  # for all model variants. 
  def spot_check(self, iternum):
    print("[INFO] Initializing model spot check for iternum " + str(iternum) + ".")
    for model_identifier in self.spot_check_dict:
      print("[INFO] Processing model variant with identifier " + str(model_identifier) + ".")
      model = self.spot_check_dict[model_identifier]
      evaluate_model = EvaluateModel(model)
      results = evaluate_model.main(iternum)

      if results is None:
        print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")
      else:
        print("[INFO] Model variant " + str(model_identifier) + " processing complete.")
        self.spot_check_results.append(str(model_identifier) + " Results: %.2f (%.2f)\n" % (results.mean()*100,results.std()*100))
    
    # All results obtained. Write to file. 
    print("[INFO] Spot check complete. Writing results to file...")
    try:
      f = open(self.spot_check_results_location + "/results.txt", "w")
      f.write("=================================\nSpot Check Results\n=================================\n\n")
      # Write model specifications
      for model_identifier in self.spot_check_dict:
        f.write(str(model_identifier) + " - ")
        model = self.spot_check_dict[model_identifier]
        for key in model:
          f.write(str(key) + ":" + str(model[key]) + "  ")
        f.write("\n")
      f.write("\n")
      # Write results of each model. 
      for result in self.spot_check_results:
        f.write(result)
      f.close()
      print("[INFO] Write complete. Have a good night...")
    except:
      print("[ERROR] Failed to write results of " + str(model_identifier) + " to file!")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  parser.add_argument('-g', action='store_true', default=False)
  args = parser.parse_args()

  iternum = int(args.iternum)
  stopGpu = args.g

  if(stopGpu is True or stopGpu is None):
    # In case you have a CUDA enabled GPU and don't want to use it. 
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 

  spot_check_dict = {
    "10001" : {
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "10002" : {
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "10003" : {
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }

  spot_check = SpotCheck(spot_check_dict)
  spot_check.spot_check(iternum)