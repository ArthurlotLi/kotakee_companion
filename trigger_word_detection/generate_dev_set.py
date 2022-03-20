#
# generate_dev_set.py
#
# Given recordings present in raw_data_kotakee_dev, generate
# X_dev_kotakee_#.npy accordingly. 
#
# Note the solution numpy arrays Y_dev_kotakee_#.npy, aka the
# labels, must be manually defined and created here. 
#
# NOTE that audacity outputs by default with metadata that 
# python's wavfile does not like. Suggest you make sure to 
# clear the wav file's metadata for each clip. 

import os
import numpy as np
from td_utils import * # The file we're using directly from the ref project.
from trigger_word_detection import TriggerWordDetection

class GenerateDevSet:
  # Constants
  Tx = 5511 # The number of time steps input to the model from the spectrogram
  n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
  Ty = 1375 # The number of time steps in the output of our model

  dev_recordings_location = "./raw_data_kotakee_dev"
  dev_output_location = "./XY_dev_kotakee"
  dev_x_name = "X_dev_kotakee.npy"
  dev_y_name = "Y_dev_kotakee.npy"

  # Small test function to refer to the dev sets given to us. 
  def check_ref_dev(self):
    original_X = "./XY_dev/X_dev.npy"
    original_Y = "./XY_dev/Y_dev.npy"
    X = np.load(original_X)
    Y = np.load(original_Y)
    print("Original X: ")
    print(X.shape)
    #print(X)
    print("Original Y: ")
    print(Y.shape)
    #print(Y)

  # Given the recordings provided in the dev_recordings_location,
  # automatically generate the X dev set npy array. Simple. Use
  # the same functions as the proper model procedure.
  #
  # Expects a dictionary of arrays, with the keys being the
  # filename and the values being arrays of timesteps (can
  # be empty) where a trigger word was just said.
  def generate_XY(self, timesteps):
    print("[INFO] Generating X and Y values for dev recordings...")

    trigger_word_detection = TriggerWordDetection()

    totalFiles = 0
    array_x = []
    array_y = []
    for filename in os.listdir(self.dev_recordings_location):
        if filename.endswith("wav"):
            # Process y by generating array from provided timestep entry. 
            if(filename not in timesteps):
              print("[INFO] No corresponding timestep entry for filename " + filename + "was found! Skipping.")
              continue
            
            # Update 11/12/21 - Do not add empty clips to the dataset to
            # encourage models that have better true positives rather than
            # true negatives. 
            if (len(timesteps[filename]) == 0):
              print("[INFO] Skipping filename " + filename + " as it contains no true positives.")
              continue

            # Process x by reading in file. 
            x = graph_spectrogram(self.dev_recordings_location + "/"+filename)
            if x.shape == (101, 5511):
              array_x.append(np.transpose(x, (1, 0)))
            else:
              print("[WARNING] File "+filename+" had an X array of incorrect shape!")
              continue

            # We are given the ms. Need to convert to ts. (x = 0.1375t) where
            # t is in milliseconds and x is the resulting timestep. 
            num_activates = 0 # For debug info only. 
            activates_string = "" # For debug info only. 

            # Initialize y (label vector) of zeros (≈ 1 line).
            y = np.zeros((1, self.Ty))

            for timestep in timesteps[filename]:
              y = trigger_word_detection.insert_ones(y, segment_end_ms=timestep)

              # Debug information
              num_activates = num_activates + 1
              segment_end_y = int(timestep * self.Ty / 10000.0)
              activates_string = activates_string + str(timestep) + "(" + str(segment_end_y) + ") "

            if y.shape == (1, 1375):
              array_y.append(np.transpose(y, (1, 0))) # We want to go from (1, 1375) to (1375, 1)
            else:
              print("[WARNING] File "+filename+" was provided a Y array of incorrect shape!")
              continue

            totalFiles = totalFiles + 1
            print("[INFO] Processed WAV file " + str(totalFiles) + " " + self.dev_recordings_location + "/"+filename + ".")
            print("       ->" + str(num_activates) + " trigger words added with timesteps: " + activates_string)

    print("[INFO] Combining all generated x arrays...")
    final_x = np.array(array_x)
    print("[INFO] Combining all generated y arrays...")
    final_y = np.array(array_y)

    print("[DEBUG] final_x.shape is:", final_x.shape)  
    print("[DEBUG] final_y.shape is:", final_y.shape)

    print("[INFO] Saving final_x to file...")
    np.save(self.dev_output_location + "/" + self.dev_x_name, final_x) 
    print("[INFO] Saving final_y to file...")
    np.save(self.dev_output_location + "/" + self.dev_y_name, final_y) 

    print("[INFO] Complete! Goodnight...")

if __name__ == "__main__":
  generate_dev_set = GenerateDevSet()
  generate_dev_set.check_ref_dev()

  # To determine the timestep of a given ms, multiply it
  # by 10,000ms/1375ts to get the ts. Provide the ms of 
  # the activation time via this timesteps dictionary and
  # the program will convert it automatically. 
  timesteps = {
    "raw_data_kotakee_dev-01.wav": [4601,9848],
    "raw_data_kotakee_dev-02.wav": [3288,8201],
    "raw_data_kotakee_dev-03.wav": [2912,8702],
    "raw_data_kotakee_dev-04.wav": [9160],
    "raw_data_kotakee_dev-05.wav": [7171],
    "raw_data_kotakee_dev-06.wav": [7338],
    "raw_data_kotakee_dev-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev-08.wav": [7886],
    "raw_data_kotakee_dev-09.wav": [5926,8219],
    "raw_data_kotakee_dev-10.wav": [3341,7832],
    "raw_data_kotakee_dev-11.wav": [7409],
    "raw_data_kotakee_dev-12.wav": [9041],
    "raw_data_kotakee_dev-13.wav": [3913],
    "raw_data_kotakee_dev-14.wav": [8624],
    "raw_data_kotakee_dev-15.wav": [7308],
    "raw_data_kotakee_dev-16.wav": [8594],
    "raw_data_kotakee_dev-17.wav": [8249],
    "raw_data_kotakee_dev-18.wav": [7403],
    "raw_data_kotakee_dev-19.wav": [8773],
    "raw_data_kotakee_dev-20.wav": [9226],
    "raw_data_kotakee_dev-21.wav": [4544,8428],
    "raw_data_kotakee_dev-22.wav": [7713],
    "raw_data_kotakee_dev-23.wav": [4622,9774],
    "raw_data_kotakee_dev-24.wav": [4205,8773],
    "raw_data_kotakee_dev-25.wav": [5908],
    "raw_data_kotakee_dev-26.wav": [],
    "raw_data_kotakee_dev-27.wav": [2787,6367],
    "raw_data_kotakee_dev-28.wav": [8475],
    "raw_data_kotakee_dev-29.wav": [7695],
    "raw_data_kotakee_dev-30.wav": [5229,8809],
    "raw_data_kotakee_dev-31.wav": [8416],
    "raw_data_kotakee_dev-32.wav": [5247],
    "raw_data_kotakee_dev-33.wav": [2823,6891],
    "raw_data_kotakee_dev-34.wav": [4199,9553],
    "raw_data_kotakee_dev-35.wav": [6385],
    "raw_data_kotakee_dev-36.wav": [5670],
    "raw_data_kotakee_dev-37.wav": [8654],
    "raw_data_kotakee_dev-38.wav": [5533],
    "raw_data_kotakee_dev-39.wav": [5855],
    "raw_data_kotakee_dev-40.wav": [2895,7052],
    "raw_data_kotakee_dev-41.wav": [5468,9476],
    "raw_data_kotakee_dev-42.wav": [6659],
    "raw_data_kotakee_dev-43.wav": [5342],
    "raw_data_kotakee_dev-44.wav": [4127,8815],
    "raw_data_kotakee_dev-45.wav": [5170],
    "raw_data_kotakee_dev-46.wav": [3115,6825],
    "raw_data_kotakee_dev-47.wav": [7242],
    "raw_data_kotakee_dev_part2-01.wav": [3672,5440],
    "raw_data_kotakee_dev_part2-02.wav": [766,4327,7398],
    "raw_data_kotakee_dev_part2-03.wav": [3926,7398],
    "raw_data_kotakee_dev_part2-04.wav": [2788,7041],
    "raw_data_kotakee_dev_part2-05.wav": [3390,6989],
    "raw_data_kotakee_dev_part2-06.wav": [967,4803,8297],
    "raw_data_kotakee_dev_part2-07.wav": [2617,4929,7227],
    "raw_data_kotakee_dev_part2-08.wav": [3836,8082],
    "raw_data_kotakee_dev_part2-09.wav": [7688],
    "raw_data_kotakee_dev_part2-10.wav": [3710,6937,9301],
    "raw_data_kotakee_dev_part2-11.wav": [2290,4721,7212,9420],
    "raw_data_kotakee_dev_part2-12.wav": [2171,4283,7011],
    "raw_data_kotakee_dev_part2-13.wav": [4431,6134,9375],
    "raw_data_kotakee_dev_part2-14.wav": [1286,4654,8015],
    "raw_data_kotakee_dev_part2-15.wav": [2543,4669,6699],
    "raw_data_kotakee_dev_part2-16.wav": [4364,6855,9041],
    "raw_data_kotakee_dev_part2-17.wav": [2164,3881,6766],
    "raw_data_kotakee_dev_part2-18.wav": [4424,6416,8379],
    "raw_data_kotakee_dev_part2-19.wav": [2297,5963,7933],
    "raw_data_kotakee_dev_part2-20.wav": [2275,6543],
    "raw_data_kotakee_dev_part2-21.wav": [2357,4736,7033],
    "raw_data_kotakee_dev_part2-22.wav": [1130,4714,7903],
    "raw_data_kotakee_dev_part2-23.wav": [3138,6699],
    "raw_data_kotakee_dev_part2-24.wav": [3227,6558],
    "raw_data_kotakee_dev_part2-25.wav": [1844,5732,9316],
    "raw_data_kotakee_dev_part2-26.wav": [2320,4305,6349,8030],
    "raw_data_kotakee_dev_part2-27.wav": [1286,3502,5576,7375],
    "raw_data_kotakee_dev_part2-28.wav": [5190],
    "raw_data_kotakee_dev_part2-29.wav": [6000,7755,9651],
    "raw_data_kotakee_dev_part2-30.wav": [3204,5368,7621],
    "raw_data_kotakee_dev_part2-31.wav": [4535,6045,8000,9636],
    "raw_data_kotakee_dev_part2-32.wav": [4550,8089],
    "raw_data_kotakee_dev_part2-33.wav": [1011,4647,8327],
    "raw_data_kotakee_dev_part2-34.wav": [1561,5435],
    "raw_data_kotakee_dev_part2-35.wav": [2208,5361,7234,8877],
    "raw_data_kotakee_dev_part2-36.wav": [1836,3673,5494,8788],
    "raw_data_kotakee_dev_part2-37.wav": [3561,5100,6825,8647],
    "raw_data_kotakee_dev_part2-38.wav": [3591,5301,7242],
    "raw_data_kotakee_dev_part2-39.wav": [],
    "raw_data_kotakee_dev_part2-40.wav": [],
    "raw_data_kotakee_dev_part2-41.wav": [3874,5636,7680],
    "raw_data_kotakee_dev_part2-42.wav": [2587,4171,6297,8357],
    "raw_data_kotakee_dev_part2-43.wav": [3145,5346,7413],
    "raw_data_kotakee_dev_part2-44.wav": [1561],
    "raw_data_kotakee_dev_part2-45.wav": [3338,8149],
    "raw_data_kotakee_dev_part2-46.wav": [1561,4112,6283,8677],
    "raw_data_kotakee_dev_part2-47.wav": [2981,4580,6520],
    "raw_data_kotakee_dev_part2-48.wav": [],
    "raw_data_kotakee_dev_part2-49.wav": [3227,5249,7294],
    "raw_data_kotakee_dev_part2-50.wav": [5881],
    "raw_data_kotakee_dev_part2-51.wav": [4171,5970,8230],
    "raw_data_kotakee_dev_part2-52.wav": [3353,5606,7792],
    "raw_data_kotakee_dev_part2-53.wav": [3420,5465,7175],
    "raw_data_kotakee_dev_part2-54.wav": [3509,7829],
    "raw_data_kotakee_dev_part2-55.wav": [2647,6468],
    "raw_data_kotakee_dev_part2-56.wav": [2788,6446],
    "raw_data_kotakee_dev_part2-57.wav": [],
    "raw_data_kotakee_dev_part2-58.wav": [3918,7822],
    "raw_data_kotakee_dev_part2-59.wav": [2654,4773,6833],
    "raw_data_kotakee_dev_part2-60.wav": [4000,5658,7480],
    "raw_data_kotakee_dev_part2-61.wav": [],
    "raw_data_kotakee_dev_part2-62.wav": [],
    "raw_data_kotakee_dev_part2-63.wav": [4372,9204],
    "raw_data_kotakee_dev_part2-64.wav": [5420],
    "raw_data_kotakee_dev_part2-65.wav": [3420,5487,7680],
    "raw_data_kotakee_dev_part2-66.wav": [2840,4907,7019],
    "raw_data_kotakee_dev_part2-67.wav": [2981,6268],
    "raw_data_kotakee_dev_part2-68.wav": [],
    "raw_data_kotakee_dev_part2-69.wav": [],
    "raw_data_kotakee_dev_part2-70.wav": [],
    "raw_data_kotakee_dev_part2-71.wav": [],
    "raw_data_kotakee_dev_part2-72.wav": [],
    "raw_data_kotakee_dev_part2-73.wav": [],
    "raw_data_kotakee_dev_part2-74.wav": [],
    "raw_data_kotakee_dev_part2-75.wav": [],
    "raw_data_kotakee_dev_part2-76.wav": [],
    "raw_data_kotakee_dev_part2-77.wav": [],
    "raw_data_kotakee_dev_part2-78.wav": [],
    "raw_data_kotakee_dev_part2-79.wav": [],
    "raw_data_kotakee_dev_part2-80.wav": [],
    "raw_data_kotakee_dev_no_negatives-01.wav": [4601,9848],
    "raw_data_kotakee_dev_no_negatives-02.wav": [3288,8201],
    "raw_data_kotakee_dev_no_negatives-03.wav": [2912,8702],
    "raw_data_kotakee_dev_no_negatives-04.wav": [9160],
    "raw_data_kotakee_dev_no_negatives-05.wav": [7171],
    "raw_data_kotakee_dev_no_negatives-06.wav": [7338],
    "raw_data_kotakee_dev_no_negatives-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev_no_negatives-08.wav": [7886],
    "raw_data_kotakee_dev_no_negatives-09.wav": [5926,8219],
    "raw_data_kotakee_dev_no_negatives-10.wav": [3341,7832],
    "raw_data_kotakee_dev_no_negatives-11.wav": [7409],
    "raw_data_kotakee_dev_no_negatives-12.wav": [9041],
    "raw_data_kotakee_dev_no_negatives-13.wav": [3913],
    "raw_data_kotakee_dev_no_negatives-14.wav": [8624],
    "raw_data_kotakee_dev_no_negatives-15.wav": [7308],
    "raw_data_kotakee_dev_no_negatives-16.wav": [8594],
    "raw_data_kotakee_dev_no_negatives-17.wav": [8249],
    "raw_data_kotakee_dev_no_negatives-18.wav": [7403],
    "raw_data_kotakee_dev_no_negatives-19.wav": [8773],
    "raw_data_kotakee_dev_no_negatives-20.wav": [9226],
    "raw_data_kotakee_dev_no_negatives-21.wav": [4544,8428],
    "raw_data_kotakee_dev_no_negatives-22.wav": [7713],
    "raw_data_kotakee_dev_no_negatives-23.wav": [4622,9774],
    "raw_data_kotakee_dev_no_negatives-24.wav": [4205,8773],
    "raw_data_kotakee_dev_no_negatives-25.wav": [5908],
    "raw_data_kotakee_dev_no_negatives-26.wav": [],
    "raw_data_kotakee_dev_no_negatives-27.wav": [2787,6367],
    "raw_data_kotakee_dev_no_negatives-28.wav": [8475],
    "raw_data_kotakee_dev_no_negatives-29.wav": [7695],
    "raw_data_kotakee_dev_no_negatives-30.wav": [5229,8809],
    "raw_data_kotakee_dev_no_negatives-31.wav": [8416],
    "raw_data_kotakee_dev_no_negatives-32.wav": [5247],
    "raw_data_kotakee_dev_no_negatives-33.wav": [2823,6891],
    "raw_data_kotakee_dev_no_negatives-34.wav": [4199,9553],
    "raw_data_kotakee_dev_no_negatives-35.wav": [6385],
    "raw_data_kotakee_dev_no_negatives-36.wav": [5670],
    "raw_data_kotakee_dev_no_negatives-37.wav": [8654],
    "raw_data_kotakee_dev_no_negatives-38.wav": [5533],
    "raw_data_kotakee_dev_no_negatives-39.wav": [5855],
    "raw_data_kotakee_dev_no_negatives-40.wav": [2895,7052],
    "raw_data_kotakee_dev_no_negatives-41.wav": [5468,9476],
    "raw_data_kotakee_dev_no_negatives-42.wav": [6659],
    "raw_data_kotakee_dev_no_negatives-43.wav": [5342],
    "raw_data_kotakee_dev_no_negatives-44.wav": [4127,8815],
    "raw_data_kotakee_dev_no_negatives-45.wav": [5170],
    "raw_data_kotakee_dev_no_negatives-46.wav": [3115,6825],
    "raw_data_kotakee_dev_no_negatives-47.wav": [7242],
    "raw_data_kotakee_dev_no_negatives_copy-01.wav": [4601,9848],
    "raw_data_kotakee_dev_no_negatives_copy-02.wav": [3288,8201],
    "raw_data_kotakee_dev_no_negatives_copy-03.wav": [2912,8702],
    "raw_data_kotakee_dev_no_negatives_copy-04.wav": [9160],
    "raw_data_kotakee_dev_no_negatives_copy-05.wav": [7171],
    "raw_data_kotakee_dev_no_negatives_copy-06.wav": [7338],
    "raw_data_kotakee_dev_no_negatives_copy-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev_no_negatives_copy-08.wav": [7886],
    "raw_data_kotakee_dev_no_negatives_copy-09.wav": [5926,8219],
    "raw_data_kotakee_dev_no_negatives_copy-10.wav": [3341,7832],
    "raw_data_kotakee_dev_no_negatives_copy-11.wav": [7409],
    "raw_data_kotakee_dev_no_negatives_copy-12.wav": [9041],
    "raw_data_kotakee_dev_no_negatives_copy-13.wav": [3913],
    "raw_data_kotakee_dev_no_negatives_copy-14.wav": [8624],
    "raw_data_kotakee_dev_no_negatives_copy-15.wav": [7308],
    "raw_data_kotakee_dev_no_negatives_copy-16.wav": [8594],
    "raw_data_kotakee_dev_no_negatives_copy-17.wav": [8249],
    "raw_data_kotakee_dev_no_negatives_copy-18.wav": [7403],
    "raw_data_kotakee_dev_no_negatives_copy-19.wav": [8773],
    "raw_data_kotakee_dev_no_negatives_copy-20.wav": [9226],
    "raw_data_kotakee_dev_no_negatives_copy-21.wav": [4544,8428],
    "raw_data_kotakee_dev_no_negatives_copy-22.wav": [7713],
    "raw_data_kotakee_dev_no_negatives_copy-23.wav": [4622,9774],
    "raw_data_kotakee_dev_no_negatives_copy-24.wav": [4205,8773],
    "raw_data_kotakee_dev_no_negatives_copy-25.wav": [5908],
    "raw_data_kotakee_dev_no_negatives_copy-26.wav": [],
    "raw_data_kotakee_dev_no_negatives_copy-27.wav": [2787,6367],
    "raw_data_kotakee_dev_no_negatives_copy-28.wav": [8475],
    "raw_data_kotakee_dev_no_negatives_copy-29.wav": [7695],
    "raw_data_kotakee_dev_no_negatives_copy-30.wav": [5229,8809],
    "raw_data_kotakee_dev_no_negatives_copy-31.wav": [8416],
    "raw_data_kotakee_dev_no_negatives_copy-32.wav": [5247],
    "raw_data_kotakee_dev_no_negatives_copy-33.wav": [2823,6891],
    "raw_data_kotakee_dev_no_negatives_copy-34.wav": [4199,9553],
    "raw_data_kotakee_dev_no_negatives_copy-35.wav": [6385],
    "raw_data_kotakee_dev_no_negatives_copy-36.wav": [5670],
    "raw_data_kotakee_dev_no_negatives_copy-37.wav": [8654],
    "raw_data_kotakee_dev_no_negatives_copy-38.wav": [5533],
    "raw_data_kotakee_dev_no_negatives_copy-39.wav": [5855],
    "raw_data_kotakee_dev_no_negatives_copy-40.wav": [2895,7052],
    "raw_data_kotakee_dev_no_negatives_copy-41.wav": [5468,9476],
    "raw_data_kotakee_dev_no_negatives_copy-42.wav": [6659],
    "raw_data_kotakee_dev_no_negatives_copy-43.wav": [5342],
    "raw_data_kotakee_dev_no_negatives_copy-44.wav": [4127,8815],
    "raw_data_kotakee_dev_no_negatives_copy-45.wav": [5170],
    "raw_data_kotakee_dev_no_negatives_copy-46.wav": [3115,6825],
    "raw_data_kotakee_dev_no_negatives_copy-47.wav": [7242],
    "raw_data_kotakee_dev_no_negatives_copy1-01.wav": [4601,9848],
    "raw_data_kotakee_dev_no_negatives_copy1-02.wav": [3288,8201],
    "raw_data_kotakee_dev_no_negatives_copy1-03.wav": [2912,8702],
    "raw_data_kotakee_dev_no_negatives_copy1-04.wav": [9160],
    "raw_data_kotakee_dev_no_negatives_copy1-05.wav": [7171],
    "raw_data_kotakee_dev_no_negatives_copy1-06.wav": [7338],
    "raw_data_kotakee_dev_no_negatives_copy1-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev_no_negatives_copy1-08.wav": [7886],
    "raw_data_kotakee_dev_no_negatives_copy1-09.wav": [5926,8219],
    "raw_data_kotakee_dev_no_negatives_copy1-10.wav": [3341,7832],
    "raw_data_kotakee_dev_no_negatives_copy1-11.wav": [7409],
    "raw_data_kotakee_dev_no_negatives_copy1-12.wav": [9041],
    "raw_data_kotakee_dev_no_negatives_copy1-13.wav": [3913],
    "raw_data_kotakee_dev_no_negatives_copy1-14.wav": [8624],
    "raw_data_kotakee_dev_no_negatives_copy1-15.wav": [7308],
    "raw_data_kotakee_dev_no_negatives_copy1-16.wav": [8594],
    "raw_data_kotakee_dev_no_negatives_copy1-17.wav": [8249],
    "raw_data_kotakee_dev_no_negatives_copy1-18.wav": [7403],
    "raw_data_kotakee_dev_no_negatives_copy1-19.wav": [8773],
    "raw_data_kotakee_dev_no_negatives_copy1-20.wav": [9226],
    "raw_data_kotakee_dev_no_negatives_copy1-21.wav": [4544,8428],
    "raw_data_kotakee_dev_no_negatives_copy1-22.wav": [7713],
    "raw_data_kotakee_dev_no_negatives_copy1-23.wav": [4622,9774],
    "raw_data_kotakee_dev_no_negatives_copy1-24.wav": [4205,8773],
    "raw_data_kotakee_dev_no_negatives_copy1-25.wav": [5908],
    "raw_data_kotakee_dev_no_negatives_copy1-26.wav": [],
    "raw_data_kotakee_dev_no_negatives_copy1-27.wav": [2787,6367],
    "raw_data_kotakee_dev_no_negatives_copy1-28.wav": [8475],
    "raw_data_kotakee_dev_no_negatives_copy1-29.wav": [7695],
    "raw_data_kotakee_dev_no_negatives_copy1-30.wav": [5229,8809],
    "raw_data_kotakee_dev_no_negatives_copy1-31.wav": [8416],
    "raw_data_kotakee_dev_no_negatives_copy1-32.wav": [5247],
    "raw_data_kotakee_dev_no_negatives_copy1-33.wav": [2823,6891],
    "raw_data_kotakee_dev_no_negatives_copy1-34.wav": [4199,9553],
    "raw_data_kotakee_dev_no_negatives_copy1-35.wav": [6385],
    "raw_data_kotakee_dev_no_negatives_copy1-36.wav": [5670],
    "raw_data_kotakee_dev_no_negatives_copy1-37.wav": [8654],
    "raw_data_kotakee_dev_no_negatives_copy1-38.wav": [5533],
    "raw_data_kotakee_dev_no_negatives_copy1-39.wav": [5855],
    "raw_data_kotakee_dev_no_negatives_copy1-40.wav": [2895,7052],
    "raw_data_kotakee_dev_no_negatives_copy1-41.wav": [5468,9476],
    "raw_data_kotakee_dev_no_negatives_copy1-42.wav": [6659],
    "raw_data_kotakee_dev_no_negatives_copy1-43.wav": [5342],
    "raw_data_kotakee_dev_no_negatives_copy1-44.wav": [4127,8815],
    "raw_data_kotakee_dev_no_negatives_copy1-45.wav": [5170],
    "raw_data_kotakee_dev_no_negatives_copy1-46.wav": [3115,6825],
    "raw_data_kotakee_dev_no_negatives_copy1-47.wav": [7242],
    "raw_data_kotakee_dev_no_negatives_copy2-01.wav": [4601,9848],
    "raw_data_kotakee_dev_no_negatives_copy2-02.wav": [3288,8201],
    "raw_data_kotakee_dev_no_negatives_copy2-03.wav": [2912,8702],
    "raw_data_kotakee_dev_no_negatives_copy2-04.wav": [9160],
    "raw_data_kotakee_dev_no_negatives_copy2-05.wav": [7171],
    "raw_data_kotakee_dev_no_negatives_copy2-06.wav": [7338],
    "raw_data_kotakee_dev_no_negatives_copy2-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev_no_negatives_copy2-08.wav": [7886],
    "raw_data_kotakee_dev_no_negatives_copy2-09.wav": [5926,8219],
    "raw_data_kotakee_dev_no_negatives_copy2-10.wav": [3341,7832],
    "raw_data_kotakee_dev_no_negatives_copy2-11.wav": [7409],
    "raw_data_kotakee_dev_no_negatives_copy2-12.wav": [9041],
    "raw_data_kotakee_dev_no_negatives_copy2-13.wav": [3913],
    "raw_data_kotakee_dev_no_negatives_copy2-14.wav": [8624],
    "raw_data_kotakee_dev_no_negatives_copy2-15.wav": [7308],
    "raw_data_kotakee_dev_no_negatives_copy2-16.wav": [8594],
    "raw_data_kotakee_dev_no_negatives_copy2-17.wav": [8249],
    "raw_data_kotakee_dev_no_negatives_copy2-18.wav": [7403],
    "raw_data_kotakee_dev_no_negatives_copy2-19.wav": [8773],
    "raw_data_kotakee_dev_no_negatives_copy2-20.wav": [9226],
    "raw_data_kotakee_dev_no_negatives_copy2-21.wav": [4544,8428],
    "raw_data_kotakee_dev_no_negatives_copy2-22.wav": [7713],
    "raw_data_kotakee_dev_no_negatives_copy2-23.wav": [4622,9774],
    "raw_data_kotakee_dev_no_negatives_copy2-24.wav": [4205,8773],
    "raw_data_kotakee_dev_no_negatives_copy2-25.wav": [5908],
    "raw_data_kotakee_dev_no_negatives_copy2-26.wav": [],
    "raw_data_kotakee_dev_no_negatives_copy2-27.wav": [2787,6367],
    "raw_data_kotakee_dev_no_negatives_copy2-28.wav": [8475],
    "raw_data_kotakee_dev_no_negatives_copy2-29.wav": [7695],
    "raw_data_kotakee_dev_no_negatives_copy2-30.wav": [5229,8809],
    "raw_data_kotakee_dev_no_negatives_copy2-31.wav": [8416],
    "raw_data_kotakee_dev_no_negatives_copy2-32.wav": [5247],
    "raw_data_kotakee_dev_no_negatives_copy2-33.wav": [2823,6891],
    "raw_data_kotakee_dev_no_negatives_copy2-34.wav": [4199,9553],
    "raw_data_kotakee_dev_no_negatives_copy2-35.wav": [6385],
    "raw_data_kotakee_dev_no_negatives_copy2-36.wav": [5670],
    "raw_data_kotakee_dev_no_negatives_copy2-37.wav": [8654],
    "raw_data_kotakee_dev_no_negatives_copy2-38.wav": [5533],
    "raw_data_kotakee_dev_no_negatives_copy2-39.wav": [5855],
    "raw_data_kotakee_dev_no_negatives_copy2-40.wav": [2895,7052],
    "raw_data_kotakee_dev_no_negatives_copy2-41.wav": [5468,9476],
    "raw_data_kotakee_dev_no_negatives_copy2-42.wav": [6659],
    "raw_data_kotakee_dev_no_negatives_copy2-43.wav": [5342],
    "raw_data_kotakee_dev_no_negatives_copy2-44.wav": [4127,8815],
    "raw_data_kotakee_dev_no_negatives_copy2-45.wav": [5170],
    "raw_data_kotakee_dev_no_negatives_copy2-46.wav": [3115,6825],
    "raw_data_kotakee_dev_no_negatives_copy2-47.wav": [7242],
    "raw_data_kotakee_dev_no_negatives_copy3-01.wav": [4601,9848],
    "raw_data_kotakee_dev_no_negatives_copy3-02.wav": [3288,8201],
    "raw_data_kotakee_dev_no_negatives_copy3-03.wav": [2912,8702],
    "raw_data_kotakee_dev_no_negatives_copy3-04.wav": [9160],
    "raw_data_kotakee_dev_no_negatives_copy3-05.wav": [7171],
    "raw_data_kotakee_dev_no_negatives_copy3-06.wav": [7338],
    "raw_data_kotakee_dev_no_negatives_copy3-07.wav": [2007, 4908, 7284],
    "raw_data_kotakee_dev_no_negatives_copy3-08.wav": [7886],
    "raw_data_kotakee_dev_no_negatives_copy3-09.wav": [5926,8219],
    "raw_data_kotakee_dev_no_negatives_copy3-10.wav": [3341,7832],
    "raw_data_kotakee_dev_no_negatives_copy3-11.wav": [7409],
    "raw_data_kotakee_dev_no_negatives_copy3-12.wav": [9041],
    "raw_data_kotakee_dev_no_negatives_copy3-13.wav": [3913],
    "raw_data_kotakee_dev_no_negatives_copy3-14.wav": [8624],
    "raw_data_kotakee_dev_no_negatives_copy3-15.wav": [7308],
    "raw_data_kotakee_dev_no_negatives_copy3-16.wav": [8594],
    "raw_data_kotakee_dev_no_negatives_copy3-17.wav": [8249],
    "raw_data_kotakee_dev_no_negatives_copy3-18.wav": [7403],
    "raw_data_kotakee_dev_no_negatives_copy3-19.wav": [8773],
    "raw_data_kotakee_dev_no_negatives_copy3-20.wav": [9226],
    "raw_data_kotakee_dev_no_negatives_copy3-21.wav": [4544,8428],
    "raw_data_kotakee_dev_no_negatives_copy3-22.wav": [7713],
    "raw_data_kotakee_dev_no_negatives_copy3-23.wav": [4622,9774],
    "raw_data_kotakee_dev_no_negatives_copy3-24.wav": [4205,8773],
    "raw_data_kotakee_dev_no_negatives_copy3-25.wav": [5908],
    "raw_data_kotakee_dev_no_negatives_copy3-26.wav": [],
    "raw_data_kotakee_dev_no_negatives_copy3-27.wav": [2787,6367],
    "raw_data_kotakee_dev_no_negatives_copy3-28.wav": [8475],
    "raw_data_kotakee_dev_no_negatives_copy3-29.wav": [7695],
    "raw_data_kotakee_dev_no_negatives_copy3-30.wav": [5229,8809],
    "raw_data_kotakee_dev_no_negatives_copy3-31.wav": [8416],
    "raw_data_kotakee_dev_no_negatives_copy3-32.wav": [5247],
    "raw_data_kotakee_dev_no_negatives_copy3-33.wav": [2823,6891],
    "raw_data_kotakee_dev_no_negatives_copy3-34.wav": [4199,9553],
    "raw_data_kotakee_dev_no_negatives_copy3-35.wav": [6385],
    "raw_data_kotakee_dev_no_negatives_copy3-36.wav": [5670],
    "raw_data_kotakee_dev_no_negatives_copy3-37.wav": [8654],
    "raw_data_kotakee_dev_no_negatives_copy3-38.wav": [5533],
    "raw_data_kotakee_dev_no_negatives_copy3-39.wav": [5855],
    "raw_data_kotakee_dev_no_negatives_copy3-40.wav": [2895,7052],
    "raw_data_kotakee_dev_no_negatives_copy3-41.wav": [5468,9476],
    "raw_data_kotakee_dev_no_negatives_copy3-42.wav": [6659],
    "raw_data_kotakee_dev_no_negatives_copy3-43.wav": [5342],
    "raw_data_kotakee_dev_no_negatives_copy3-44.wav": [4127,8815],
    "raw_data_kotakee_dev_no_negatives_copy3-45.wav": [5170],
    "raw_data_kotakee_dev_no_negatives_copy3-46.wav": [3115,6825],
    "raw_data_kotakee_dev_no_negatives_copy3-47.wav": [7242],
  }

  generate_dev_set.generate_XY(timesteps)