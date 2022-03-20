#
# speech_speak_subprocess.py
#
# Subprocess companion for speech_speak. Unfortunately working with
# pyttsx3 and threads means that it's very difficult (impossible?) 
# to detect when a speech execution has completed. So we're using
# multiprocessing. 
# 
# Also uses the multiprocessing library to recieve information 
# from the main program via it's wrapped socket library. 

from multiprocessing.connection import Listener
import pyttsx3

import sys
import socketserver

class SpeechSpeakSubprocess:
  subprocess_address = "localhost"
  subprocess_port = 0 # Selected by OS
  subprocess_key = b"speech_speak"
  
  shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 
  stop_process = False

  engine = None
  listener = None

  def __init__(self): 
    self.engine = pyttsx3.init()

    # Find a open port (unfortunately multiprocessing.connection does
    # not do this for us.) Source:
    # https://stackoverflow.com/questions/1365265/on-localhost-how-do-i-pick-a-free-port-number
    with socketserver.TCPServer((self.subprocess_address, 0), None) as s:
      self.subprocess_port = s.server_address[1]

    address = (self.subprocess_address, self.subprocess_port)

    # Output to the pipe that the main process is listening through.
    print(str(self.subprocess_port) + "/")
    sys.stdout.flush()

    # Now we can output business as usual. 
    sys.stdout = sys.__stdout__
    print("[DEBUG] Speech Speak Subprocess initializing with address: ")
    print(address)

    self.listener = Listener(address, authkey=self.subprocess_key)
    print("[DEBUG] Speech Speak Subprocess Listener successfully created.")

  def listen_for_connection(self):
    connection = self.listener.accept()
    # Connection accepted. Execute the input text before replying
    # with a finished message. 
    input_text = connection.recv()
    if input_text == self.shutdown_code:
      self.stop_process = True
      return
    self.execute_text(input_text)
    connection.send("200") # Contents of the message don't matter. 
    connection.close()
    
  # Blocking execution of the given input text. 
  def execute_text(self, input_text):
    self.engine.say(input_text)
    self.engine.runAndWait() # Blocks the thread until it completes.

# Execution code - listen indefinitely for connections and 
# execute incoming text. 
speech_speak_subprocess = SpeechSpeakSubprocess()
while speech_speak_subprocess.stop_process is False:
  speech_speak_subprocess.listen_for_connection()

print("[DEBUG] Speech Speak subprocess shut down successfully.")