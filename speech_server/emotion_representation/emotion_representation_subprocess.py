#
# emotion_representation_subprocess.py
#
# Subprocess companion for emotion_representation. OpenCV does not
# run in a non-main thread for non-windows platforms, hence this
# subprocess. This process runs in parallel to the main process,
# handling requests to run videos and stop videos having been
# initialized once at startup. 
# 
# Also uses the multiprocessing library to recieve information 
# from the main program via it's wrapped socket library. 

from multiprocessing.connection import Listener

import cv2
import sys
import socketserver
import threading
import time

class EmotionRepresentationSubprocess:
  video_window_text = "KotakeeOS - Textual Emotion Representation"

  subprocess_address = "localhost"
  subprocess_port = 0 # Selected by OS
  subprocess_key = b"emotion_representation"
  
  shutdown_code = "SHUTDOWN" # No incoming text should be called this. 
  stop_video_code = "STOP_VIDEO" # Stop a playing video.
  stop_process = False

  listener = None
  video_location = None
  new_video = False
  listen_for_connection_thrd_instance = None

  # In s, how long to wait between checks to see if the video_location
  # is not None. 
  wait_for_connection_duration = 0.050

  # How fast the videos run: ms delay between frames. For example,
  # for 24 fps (24 in 1000 ms), you'd set this delay to 42.
  video_delay_ms = 30

  def __init__(self): 
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
    print("[DEBUG] Emotion Representation Subprocess initializing with address: ")
    print(address)

    self.listener = Listener(address, authkey=self.subprocess_key)
    print("[DEBUG] Emotion Representation Subprocess Listener successfully created.")

    self.start_listen_for_connection_thrd()

  def start_listen_for_connection_thrd(self):
    self.listen_for_connection_thrd_instance = threading.Thread(target=self.listen_for_connection_thrd, daemon=True).start()
    print("[DEBUG] Emotion Representation Subprocess connection thread successfully created.")

  # Is in charge of communicating with the main process and adjusting
  # runtime flags accordingly. 
  def listen_for_connection_thrd(self):
    while self.stop_process is False:
      self.listen_for_connection()

  # Listen for an incoming message from the main process. Use a try
  # except for whack behavior of running a multiprocessing recv for
  # prolonged periods of time (i.e. hours/days).
  def listen_for_connection(self):
    try:
      connection = self.listener.accept()
      # Connection accepted. Execute the video. 
      input_text = connection.recv()
      if input_text == self.shutdown_code:
        print("[DEBUG] Emotion Representation Subprocess received SHUTDOWN request.")
        self.stop_process = True
      elif input_text == self.stop_video_code:
        # Stop the video.
        print("[DEBUG] Emotion Representation Subprocess clearing video location.")
        self.video_location = None
      else:
        # Start the video (or override it)
        print("[DEBUG] Emotion Representation Subprocess received video location '" + input_text + "'.")
        if self.video_location is None or self.video_location != input_text:
          # Do not replace video if location is the exact same as the
          # current playing video. 
          self.video_location = input_text
          self.new_video = True
      
      # All done. End the interaction. 
      connection.close()
    except Exception as e:
      print("[ERROR] Emotion Representation Subprocess listen for connection ran into an exception:" )
      print(e)
    
  # Indefinite video loop. 
  def run_video_indefinitely(self):
    print("[DEBUG] Emotion Representation Subprocess starting video runtime loop.")
    try:
      while self.stop_process is False:
        if (self.video_location is None):
          # No video to play. Wait.
          time.sleep(self.wait_for_connection_duration)
        else:
          # Video found! Play the video endlessly until it's set to
          # None again. 

          # In order to address peculiarities with Linux/Mac and Cv2
          # windows, start the window thread first. 
          #
          # https://stackoverflow.com/questions/6116564/destroywindow-does-not-close-window-on-mac-using-python-and-opencv
          if self.new_video is False:
            cv2.namedWindow(self.video_window_text)
            cv2.startWindowThread()
          else:
            # Reset the boolean. We're opening the new video now. 
            self.new_video = False

          cap = cv2.VideoCapture(self.video_location)
          if cap.isOpened() is False: 
            print("[ERROR] Emotion Representation Error opening video file at '" + self.video_location + "'.")
            
          while(cap.isOpened() and self.stop_process is False and self.video_location is not None and self.new_video is False):
            # Read and capture video frame by frame. 
            ret, frame = cap.read() 

            if ret:
                cv2.imshow(self.video_window_text, frame)
            else:
              # End of the video reached - repeat the video. 
              cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
              continue

            if cv2.waitKey(self.video_delay_ms) & 0xFF == ord('q'):
              break
          
          # Clear the video. 
          cap.release()

          if self.new_video is False:
            # Don't delete the window if we've been given another video
            # to replace the current one. 
            cv2.waitKey(1)
            cv2.destroyAllWindows()
            cv2.waitKey(1)
    except Exception as e:
      print("[ERROR] Emotion Representation subprocess ran into an fatal exception! Exception text:")
      print(e)

# Execution code - listen indefinitely for connections and 
# execute incoming text. 
emotion_representation_subprocess = EmotionRepresentationSubprocess()
emotion_representation_subprocess.run_video_indefinitely()

print("[DEBUG] Emotion Representation subprocess shut down successfully.")