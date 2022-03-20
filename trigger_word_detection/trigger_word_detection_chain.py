#
# trigger_word_detection_chain.py
#
# Allows for multiple training sessions to occur at once utilizing
# class defined in trigger_word_detection.py. Utilizes processes
# to circumvent graphics card memory flushing issue for keras. 
#
# Note: expects all datasets to have been generated already. 

# TODO: Implement process usage to properly allow for multiple large-dataset training sessions to occur consecutively. 

from trigger_word_detection import TriggerWordDetection
 
import os
import multiprocessing
import time

class TriggerWordDetectionChain:

  chain_train_results_location = "./chain_train_results"
  chain_train_results = []
  chain_train_dict = None

  def __init__(self, models_dict):
    self.chain_train_dict = models_dict

  def execute_chain_train(self):
    print("[INFO] Initializing Trigger Word Detection Chain Train...")
    for model_identifier in self.chain_train_dict:
      try:
        print("\n[INFO] Processing model variant with identifier " + str(model_identifier) + ".")
        model = self.chain_train_dict[model_identifier]
        time_start = time.time()

        # Execute training as a separate process. Use a queue to
        # obtain results. 
        ret_dict = {"best_accuracy":None, "acc":None}
        queue = multiprocessing.Queue()
        queue.put(ret_dict)

        print("[INFO] Executing new process...")
        p = multiprocessing.Process(target=self.trigger_word_detection_worker, args=(queue, model, model_identifier,))
        p.start()
        p.join()
        ret_dict_result = queue.get()
        print("\n[INFO] Process complete; result: ")
        print(ret_dict_result)
        best_accuracy = ret_dict_result["best_accuracy"]
        acc = ret_dict_result["acc"]

        time_end = time.time()
        time_elapsed_seconds = time_end - time_start # time in seconds. 
        time_elapsed_hours = time_elapsed_seconds/3600 

        if best_accuracy is None or acc is None:
          print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")
          self.chain_train_results.append(str(model_identifier) + " EXECUTION FAILED!\n")
        else:
          print("[INFO] Model variant " + str(model_identifier) + " processing complete.")
          self.chain_train_results.append(str(model_identifier) + " Train Accuracy: %.8f Dev Accuracy: %.8f Time: %.4f hrs\n" % (best_accuracy*100,acc*100, time_elapsed_hours))
      except:
        # Use a try/except so that we still write the remaining stuff 
        # to file in case of a failure or the user cancels the rest.
        print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")

    # All results obtained. Write to file. 
    self.write_results()

  # Executed as a separate process so it can be purged as a
  # seperate process, allowing Tensorflow to clear out the
  # memory of the GPU and not freak out when we train another
  # right after.
  def trigger_word_detection_worker(self, queue, model, model_identifier):
    trigger_word_detection = TriggerWordDetection(model_parameters=model)
    best_accuracy, acc = trigger_word_detection.main(iternum = int(model["iternum"]), outputnum = model_identifier)
    ret_dict = queue.get()
    ret_dict["best_accuracy"] = best_accuracy
    ret_dict["acc"] = acc
    queue.put(ret_dict)
    
  def write_results(self):
    try:
      results_folder_contents = os.listdir(self.chain_train_results_location)
      result_index = 0
      file_name_prefix = "chain_train_results_"
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

      filename = self.chain_train_results_location + "/"+file_name_prefix+str(result_index)+file_name_suffix
      f = open(filename, "w")
      print("\n[INFO] Chain train complete. Writing results to file '"+filename+"'...")
      f.write("=================================\nChain Train Results\n=================================\n\n")
      # Write model specifications
      for model_identifier in self.chain_train_dict:
        f.write(str(model_identifier) + " - ")
        model = self.chain_train_dict[model_identifier]
        for key in model:
          f.write(str(key) + ":" + str(model[key]) + "  ")
        f.write("\n")
      f.write("\n")
      # Write results of each model. 
      for result in self.chain_train_results:
        f.write(result)
      f.close()
      print("[INFO] Write complete. Have a good night...")
    except:
      print("[ERROR] Failed to write results of " + str(model_identifier) + " to file!")

if __name__ == "__main__":

  # Each model identifier is the outputnum that the model wil be
  # saved as (don't let this overwrite other models.) The iternum
  # specified in each model's arguments refers to the dataset number
  # that will be used. 
  #
  # Note that the only required field is the iternum - defaults will
  # be used for other fields if not specified. 
  chain_dict = {
    "14220" : {
      "iternum" : "13940",
      "model_learning_rate" : 0.00017,
      "model_epochs" : 10000,
      "dataset_size" : 9000,
      "max_negatives" : 4,
      "model_conv1d": 256,
      "model_gru_1": 256,
      "model_gru_2": 256,
      "model_hidden_dropout":0.5,
      "model_l2":True,
      "model_l2_influence": 0.000001,
    },
  }

  trigger_word_detection_chain = TriggerWordDetectionChain(chain_dict)
  trigger_word_detection_chain.execute_chain_train()
