#
# raw_data_utils.py
#
# Tiny little script to handle randomly handpicking files from the
# raw_data_lingua_libre dataset and inserting them into 
# raw_data/negatives. That's because I only want a certain number
# of samples from the lingua libre dataset but I also want it to
# be generally varied. 

import os
import numpy as np

from_directory = "./raw_data_lingua_libre"
to_directory = "./raw_data/negatives"
number_of_negatives = 5000
#number_of_negatives = 200

def cherry_pick_lingua_libre():
  print("[INFO] Initializing cherry_pick_lingua_libre...")

  promptInput = None
  while promptInput is None or (promptInput != "y" and promptInput != "n"):
    promptInput = input("[NOTICE] This program will copy " +str(number_of_negatives)+" file(s) from " + from_directory +" to " + to_directory +". Continue? (y/n)\n")
    promptInput = promptInput.lower()
    
  if promptInput == "y":
    totalFiles = 0
    negatives = []
    for filename in os.listdir(from_directory):
      if filename.endswith("wav"):
        negatives.append(filename)

        totalFiles = totalFiles + 1
    
    print("[INFO] File parsing complete. Total files is " + str(totalFiles) + ".")
  
    # All files are now in negatives. Cherry picking time. 
    random_indices = np.random.randint(len(negatives), size=number_of_negatives)
    random_negatives = [negatives[i] for i in random_indices]
    for random_negative in random_negatives:
      # Mac: 
      # command = 'cp ' + from_directory + "/" + random_negative + ' ' + to_directory + "/" + random_negative
      # Windows:
      command = 'xcopy "' + from_directory + '/' + random_negative + '" "' + to_directory  + '/" /F /C /K /O /Y'
      print("[INFO] Executing command: " + command)
      os.system(command)


if __name__ == "__main__":
  cherry_pick_lingua_libre()