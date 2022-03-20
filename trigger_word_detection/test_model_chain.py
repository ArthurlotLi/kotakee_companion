#
# test_model_chain.py
#
# Tests all models currently present in a specified directory
# given the class defined in test_model. 

from struct import pack_into

from cv2 import drawFrameAxes
from test_model import TestModel
 
import os
import multiprocessing
import argparse
import numpy as np

from matplotlib import pyplot as plt
import pandas as pd

class TestModelChain:
  X_dev_location = "./XY_dev_kotakee/X_dev_kotakee.npy"
  Y_dev_location = "./XY_dev_kotakee/Y_dev_kotakee.npy"

  chain_test_results_location = "./chain_test_results"
  chain_test_results = {}
  chain_test_results_acc_map = {}
  test_model_location = None

  minibatch_size = 1
  use_gpu = True # If using GPU, the minbatch will automatically be set to 1. 

  def __init__(self, location):
    self.test_model_location = location

  def execute_chain_test(self):
    print("[INFO] Initializing Test Model Chain...")
    filename_uid = 0 # for sorting.

    X_dev = None
    Y_dev = None

    # Load the dev datset once and pass to all workers.  
    try:
      print("[INFO] Loading dev dataset X file " + self.X_dev_location + "...")
      X_dev = np.load(self.X_dev_location)
      print("[INFO] Loading dev dataset Y file " + self.Y_dev_location + "...")
      Y_dev = np.load(self.Y_dev_location)
      print("[DEBUG] X_dev.shape is:", X_dev.shape)  
      print("[DEBUG] Y_dev.shape is:", Y_dev.shape) 
    except:
      print("[WARN] Error loading X_dev and/or Y/dev.")
      return -1

    minibatch = []
    
    files = os.listdir(self.test_model_location)

    # If using GPU, the minbatch will automatically be set to 1. 
    if self.use_gpu:
      self.minibatch_size = 1

    for j in range(0, len(files)):
      filename = files[j]
      if filename.endswith("h5"):
        minibatch.append(filename)
      # If a minibatch has been filled OR we're at the end of files. 
      if len(minibatch) == self.minibatch_size or j == len(files)-1:
        try:
          print("[INFO] Processing minibatch: " + str(minibatch))
          ret_dict = {}
          queue = multiprocessing.Queue()
          queue.put(ret_dict)

          minibatch_processes = {}

          for i in range(0, len(minibatch)):
            file = minibatch[i]
            print("[INFO] Creating new subprocess for model " + str(file) + ".")
            
            # Execute test as a separate process. Use a queue to
            # obtain results. 
            p = multiprocessing.Process(target=self.test_model_worker, args=(queue, self.test_model_location + "/" + file, X_dev, Y_dev, "acc" + str(i)))
            minibatch_processes[i] = (p, file)

          # After all of the processes have been created. Kick off in parallel.
          for item in minibatch_processes:
            tuple = minibatch_processes[item]
            print("\n\n[INFO] Executing new process for model " + tuple[1] + ".\n")
            tuple[0].start()

          # Now wait for all of them.
          for p in minibatch_processes:
            tuple[0].join()
          ret_dict_result = queue.get()
          print("\n[INFO] Processes complete; results:")
          print(ret_dict_result) 
          print("")
          for item in ret_dict_result:
            item_identifier = int(item.replace("acc",""))
            if item_identifier in minibatch_processes:
              filename = minibatch_processes[int(item.replace("acc",""))][1]
              acc = ret_dict_result[item]
            
              if acc is None:
                print("[WARN] Received empty acc!")
                self.chain_test_results[filename_uid] = "00.00000000 - " + str(filename) + " TEST FAILED!\n"
                self.chain_test_results_acc_map[-1] = filename_uid
              else:
                self.chain_test_results[filename_uid] = "%.8f - " % (acc*100) + str(filename) + "\n"
                # If a model of that exact accuracy exists already, append
                # a tiny number to it until it's unique. 
                if acc in self.chain_test_results_acc_map:
                  sorting_acc = None
                  while sorting_acc is None:
                    acc = acc + 0.000000000000001 # Acc has 15 decimal precision. Append by 1 to break ties.
                    if acc not in self.chain_test_results_acc_map:
                      sorting_acc = acc
                  self.chain_test_results_acc_map[sorting_acc] = filename_uid
                else:
                  self.chain_test_results_acc_map[acc] = filename_uid
              
              filename_uid = filename_uid + 1
            
          print("\n[INFO] Minibatch: " + str(minibatch) + " processing complete.\n")
        except Exception as e:
          # Use a try/except so that we still write the remaining stuff 
          # to file in case of a failure or the user cancels the rest.
          print("\n\n[ERROR] !!!! Failed to process model " + str(filename) + "! Exception:")
          print(e)
          print("\n")
        minibatch = []

    if(filename_uid == 0):
      print("[WARNING] No models found at location '" + self.test_model_location + "'. Please specify another location with an argument (example: python test_model_chain.py ./model_checkpoints) or move/copy the model(s) accordingly.")
      return

    # Sort the results.
    self.chain_test_results_acc_map = dict(sorted(self.chain_test_results_acc_map.items(), key=lambda item: item[0]))

    # All results obtained. Write to file. 
    self.write_results()

  # Executed as a separate process so it can be purged as a
  # seperate process, allowing Tensorflow to clear out the
  # memory of the GPU and not freak out when we train another
  # right after. If the GPU is disabled, this still allows the 
  # memory to be handled properly. 
  def test_model_worker(self, queue, model_path, X_dev = None, Y_dev = None, acc_dict_name = "acc"):
    test_model = TestModel()
    acc = test_model.test_model(model_path = model_path, X_dev = X_dev, Y_dev = Y_dev, use_gpu = self.use_gpu)
    ret_dict = queue.get()
    ret_dict[acc_dict_name] = acc
    queue.put(ret_dict)
    
  def write_results(self):
    try:
      results_folder_contents = os.listdir(self.chain_test_results_location)
      result_index = 0
      file_name_prefix = "chain_test_results_"
      file_name_suffix = ".txt"
      for file in results_folder_contents:
        file_number_str = file.replace(file_name_prefix, "").replace(file_name_suffix, "")
        file_number = -1
        try:
          file_number = int(file_number_str)
          if(file_number >= result_index):
            result_index = file_number + 1
        except:
          print("[WARN] Unexpected file in results directory. Ignoring...")

      filename = self.chain_test_results_location + "/"+file_name_prefix+str(result_index)+file_name_suffix
      f = open(filename, "w")
      print("\n[INFO] Chain test complete. Writing results to file '"+filename+"'...")

      f.write("=================================\nSORTED Chain Test Results\n=================================\n\n")
      # Write results of each model, sorted.
      for key in self.chain_test_results_acc_map:
        f.write(self.chain_test_results[self.chain_test_results_acc_map[key]])

      f.close()
    except:
      print("[ERROR] Failed to write results to file!")
    
    self.graph_history(filename=filename)

    print("[INFO] Write complete. Have a good night...")

  # Given all the test accuracies that we've generated, let's 
  # graph every single one. Note that we expect a very specific
  # file name structure for these model iterations:
  #
  # tr_model_'+str(modelnum)+'_{val_accuracy:.5f}_{accuracy:.5f}_{epoch:02d}' + ".h5"
  # Ex) tr_model_14100_0.99662_0.99613_502.h5
  #
  # Expects full location of the file that has been written -
  # the suffix will be stripped but otherwise the graph will be
  # written to file with that exact name. 
  def graph_history(self, filename):
    print("[INFO] Generating test acc history graph.")

    graph_width_inches = 13
    graph_height_inches = 7
    
    graph_location = filename.replace(".txt", "")

    title = "Chain Test Accuracy History"
    fig = plt.figure(1)
    fig.suptitle(title)
    fig.set_size_inches(graph_width_inches,graph_height_inches)

    # Gather points. Every point should be indexed by epoch. 
    indices = []
    test_accs = []
    val_accs = []
    train_accs = []

    # Each item should be structured as such:
    # 99.69913960 - tr_model_14060_0.99860_0.99981_2076.h5
    for key in self.chain_test_results_acc_map: 
      string = self.chain_test_results[self.chain_test_results_acc_map[key]]
      try:
        epoch = None
        test_acc = None
        val_acc = None
        train_acc = None

        string_split_apos = string.split(" - ")
        test_acc = float(string_split_apos[0].strip())

        result_string_split = string_split_apos[1].split("_")
        epoch = int(result_string_split[5].split(".h")[0].strip())
        val_acc = float(result_string_split[3].strip())*100
        train_acc = float(result_string_split[4].strip())*100
        
        indices.append(epoch)
        test_accs.append(test_acc)
        val_accs.append(val_acc)
        train_accs.append(train_acc)
      except Exception as e:
        print("[WARNING] Encountered an exception while parsing string " + str(string) + ":")
        print(e)

    # We now have everything in our arrays. Combine them to graph 
    # them.   
    data= []
    for i in range(0, len(indices)):
      data.append([indices[i], test_accs[i], val_accs[i], train_accs[i]])

    df = pd.DataFrame(data, columns = ["epoch", "test_acc", "val_acc", "train_acc"])

    # Sort the dataframe by epoch first so lines are drawn properly.
    df.sort_values("epoch", axis=0, inplace=True)

    df.set_index("epoch", drop=True, inplace=True)
    df = df.astype(float)

    # With our dataframe, we can finally graph the history. 
    plt.plot(df["val_acc"])
    plt.plot(df["test_acc"])
    plt.plot(df["train_acc"])
    plt.ylabel("Accuracy")
    plt.xlabel("Epoch")
    plt.legend(["val_acc", "test_acc", "train_acc"], loc="upper left")

    # Save the graph. 
    try:
      fig.savefig(graph_location)
      print("[DEBUG] Graph successfully saved to: " + str(graph_location) + ".")
    except Exception as e:
      print("[ERROR] Unable to save graph at location: " + str(graph_location) + ". Exception:")
      print(e)
    
    plt.close("all")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # Add a '?' to make the argument optional
  parser.add_argument("location", nargs='?', default="./model_chain_test")
  args = parser.parse_args()

  location = args.location

  test_model_chain = TestModelChain(location)
  test_model_chain.execute_chain_test()
