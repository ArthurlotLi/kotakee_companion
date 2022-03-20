#
# generate_test_set.py
#
# Tiny little script to handle randomly handpicking files from the
# raw_data/activates folder and moving them into 
# raw_data_dev/activates. This is to generate the test set with 
# a specified % split. 

import os
from numpy.random import default_rng

from_directory = ".\\raw_data\\activates"
to_directory = ".\\raw_data_dev\\activates"
percent_split = 10

def generate_test_set():
  print("[INFO] Initializing cherry_pick_lingua_libre...")

  promptInput = None
  while promptInput is None or (promptInput != "y" and promptInput != "n"):
    promptInput = input("[NOTICE] This program will move " +str(percent_split)+" percent of file(s) from " + from_directory +" to " + to_directory +". Continue? (y/n)\n")
    promptInput = promptInput.lower()
    
  if promptInput == "y":
    totalFiles = 0
    activates = []
    for filename in os.listdir(from_directory):
      if filename.endswith("wav"):
        activates.append(filename)

        totalFiles = totalFiles + 1

    files_to_move = totalFiles//10
    
    print("[INFO] File parsing complete. Total files is " + str(totalFiles) + ". Files to be moved: " + str(files_to_move) + ".")
  
    # All files are now in activates. Cherry picking time. 
    rng = default_rng()
    #random_indices = np.random.randint(len(activates), size=files_to_move)
    random_indices = rng.choice(len(activates), size=files_to_move, replace=False) # Sample without replacement. 
    random_negatives = [activates[i] for i in random_indices]
    for random_negative in random_negatives:
      # Mac: 
      # ???
      # Windows:
      command = 'move "' + from_directory + '\\' + random_negative + '" "' + to_directory
      print("[INFO] Executing command: " + command)
      os.system(command)


if __name__ == "__main__":
  generate_test_set()