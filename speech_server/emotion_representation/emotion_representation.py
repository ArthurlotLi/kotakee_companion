#
# emotion_representation.py
#
# A companion project to Emotion Detection AI - given an emotion
# category, display a visual simulation of the corresponding 
# emotion. 
#
# Intended to be integrated in with Kotakee Speech Server's 
# Speech Speak so that every time any text is provided to the
# user, an emotion is provided with it in the form of one of 
# the videos we'll play from here. 
#
# A pretty silly way to use a legitimately useful model. 

import os
import time
from subprocess import Popen, PIPE
from multiprocessing.connection import Client

class EmotionRepresentation:
  # Relative to speech_speak.py. May pass in an override for this.
  emotion_videos_location = "./emotion_representation/emotion_media"

  windows_platform = None

  # Utilize a subprocess instead of hosting opencv via a subthread. 
  # In the interest of maintainability, lock the subprocess usage to
  # always on. 
  use_subprocess = True

  # We use multiprocessing to output opencv visuals.
  subprocess_location = "./emotion_representation/emotion_representation_subprocess.py"
  subprocess_address = "localhost"
  subprocess_port = 0 # OS Selected - we expect this from the subprocess on startup. 
  subprocess_key = b"emotion_representation"
  subprocess_instance = None
  subprocess_shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 
  subprocess_stop_video_code = "STOP_VIDEO" # Stop a playing video.
  
  # Maintained so we know what we're currently showing (if any)
  subprocess_current_video = None
  subprocess_emotion_state = None

  # Addressing the command line call to execute the subprocess.
  # Try using python3 first, and if that fails, remember and use
  # python instead.
  use_python3 = None

  # Reduced emotion detection will NOT display idle animations. 
  use_emotion_representation_reduced = None

  # Provide maps from emotion category strings to the actual 
  # Blender 3D Character renders depicting someone expressing
  # that emotion while talking. There are three separate 
  # categories dependent on the time of day (a nice little touch
  # imo)
  #
  # All videos have frame ranges 0 to 120, hence the 0000-0120 
  # suffix. (I couldn't bother to rename the blender outputs.)

  emotion_video_map_sunlight = {
    "joy":"sunlight_joy0000-0120.mp4",
    "sadness":"sunlight_sadness0000-0120.mp4",
    "fear":"sunlight_fear0000-0120.mp4",
    "anger":"sunlight_anger0000-0120.mp4",
    "disgust":"sunlight_disgust0000-0120.mp4",
    "surprise":"sunlight_surprise0000-0120.mp4",
    "neutral":"sunlight_neutral0000-0120.mp4",
    "idle1":"sunlight_idle10000-0240.mp4",
    "listen":"sunlight_listen0000-0120.mp4",
  }
  emotion_video_map_nightlight = {
    "joy":"nightlight_joy0000-0120.mp4",
    "sadness":"nightlight_sadness0000-0120.mp4",
    "fear":"nightlight_fear0000-0120.mp4",
    "anger":"nightlight_anger0000-0120.mp4",
    "disgust":"nightlight_disgust0000-0120.mp4",
    "surprise":"nightlight_surprise0000-0120.mp4",
    "neutral":"nightlight_neutral0000-0120.mp4",
    "idle1":"nightlight_idle10000-0240.mp4",
    "listen":"nightlight_listen0000-0120.mp4",
  }
  emotion_video_map_sunset = {
    "joy":"sunset_joy0000-0120.mp4",
    "sadness":"sunset_sadness0000-0120.mp4",
    "fear":"sunset_fear0000-0120.mp4",
    "anger":"sunset_anger0000-0120.mp4",
    "disgust":"sunset_disgust0000-0120.mp4",
    "surprise":"sunset_surprise0000-0120.mp4",
    "neutral":"sunset_neutral0000-0120.mp4",
    "idle1":"sunset_idle10000-0240.mp4",
    "listen":"sunset_listen0000-0120.mp4",
  }

  # Default sunset time and duration. This may be passed into the 
  # emotion function and overridden if the data is queried from
  # sources like the OpenWeatherMapAPI. 
  #
  # A sunset time will be set at the middle of the duration.
  sunset_default_time_hours = 17
  sunset_default_time_minutes = 00
  
  # Same deal for sunrise. 
  sunrise_default_time_hours = 6
  sunrise_default_time_minutes = 30

  sunset_sunrise_duration = 60

  def __init__(self, emotion_videos_location = None, subprocess_location = None, use_python3 = True, use_emotion_representation_reduced = False):
    self.use_python3 = use_python3
    self.use_emotion_representation_reduced = use_emotion_representation_reduced

    # Path customization
    if emotion_videos_location is not None:
      self.emotion_videos_location = emotion_videos_location
    if subprocess_location is not None:
      self.subprocess_location = subprocess_location

    # Keep this flag for path manipulation.
    if (os.name == "nt"):
      self.windows_platform = True
    else:
      self.windows_platform = False

    if self.use_subprocess:
      # Initialize the subprocess.
      if self.initialize_subprocess() is False:
        print("[ERROR] Failed to initialize subprocess. Emotion Representation initialization failed.")  
        return

  # Initializes the subprocess.
  def initialize_subprocess(self):
    # Use subprocess Popen as we don't want to block for a 
    # process we want to keep running. We'll interact with it
    # using multiprocessing's wrapped sockets. 

    if self.use_python3 is True:
      self.subprocess_instance = Popen(["python3", self.subprocess_location, ""], stdout=PIPE, bufsize=1, universal_newlines=True)
    else:
      self.subprocess_instance = Popen(["python", self.subprocess_location, ""], stdout=PIPE, bufsize=1, universal_newlines=True)

    print("[DEBUG] Emotion Representation subprocess spawned successfully.")
    self.wait_for_subprocess_port()

    return True

  # Read the stdout of the subprocess until we get a complete port. 
  # output should be terminated by / character. Ex) 42312/
  def wait_for_subprocess_port(self):
    print("[DEBUG] Waiting for subprocess port number...")
    read_full_output = False
    complete_output = ""
    while read_full_output is False:
      output = self.subprocess_instance.stdout.readline()
      if output:
        complete_output = complete_output + output
        if "/" in complete_output:
          port_number = int(complete_output.replace("/", ""))
          print("[DEBUG] Successfully recieved subprocess port number: " + str(port_number))
          self.subprocess_port = port_number
          read_full_output = True
          return True
    return False

  def shutdown_process(self):
    if self.use_subprocess:
      print("[DEBUG] Emotion Representation shutting down existing process.")
      # Socket interaction using multiprocessing library. 
      address = (self.subprocess_address, self.subprocess_port)
      connection = Client(address, authkey=self.subprocess_key)
      connection.send(self.subprocess_shutdown_code)
      connection.close()

  # Expects a solution string directly from the output of the
  # emotion detection model (Ex) "joy"). Remember we're using Paul
  # Ekman's Discrete Emotion Model + "neutral".
  #
  # OBSOLETE. Replaced by subprocess implementation. Kept around 
  # in case of future testing in other platforms. 
  def display_emotion_simple(self, emotion_category, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration= None):
    if emotion_category in self.emotion_video_map_sunlight:

      # Get the video location. 
      video_location = self.derive_video_location(
        emotion_category=emotion_category,  
        sunrise_hours = sunrise_hours, 
        sunrise_minutes = sunrise_minutes, 
        sunset_hours = sunset_hours, 
        sunset_minutes = sunset_minutes,
        sunset_sunrise_duration = sunset_sunrise_duration)

      # Play the video. For now let's just use the simple startfile
      # with no way of knowing when it finishes and/or being able
      # to cancel it. 
      print("[DEBUG] Emotion Representation using video located at: " + video_location + ".")
      try:
        if (self.windows_platform):
          os.startfile(video_location)
        else:
          # Assumed mac. 
          # TODO: Currently FAR TOO MUCH HASSLE to get VLC working
          # on mac, especially considering this is a temporary measure. 
          pass 
      except Exception as e:
        print("[ERROR] Emotion Representation failed to play video! Exception: ")
        print(e)
    else:
      print("[ERROR] Emotion Representation does not support emotion '"+ str(emotion_category) + "'!")
  
  # Start displaying an emotion on the emotion representation subprocess. 
  # This means that we're actively "talking" right now. We later expect
  # stop_display_emotion in order to stop talking. 
  def start_display_emotion(self, emotion_category, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration= None):
    if emotion_category in self.emotion_video_map_sunlight:
      # Get the video location. 
      video_location = self.derive_video_location(
        emotion_category=emotion_category,  
        sunrise_hours = sunrise_hours, 
        sunrise_minutes = sunrise_minutes, 
        sunset_hours = sunset_hours, 
        sunset_minutes = sunset_minutes,
        sunset_sunrise_duration = sunset_sunrise_duration)

      # We have the filename. Send the subprocess the video to play. 
      self.send_video_to_subprocess(video_location=video_location, emotion_category = emotion_category)
      # The process has the video and is playing it now. 
    else:
      print("[ERROR] Emotion Representation does not support emotion '"+ str(emotion_category) + "'!")
  
  # Stop displaying emotion.
  def stop_display_emotion(self, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration= None):
    if self.use_emotion_representation_reduced:
      self.clear_display_emotion()
    else:
      # Play idle animation. 
      video_location = self.derive_video_location(
        emotion_category="idle1",  
        sunrise_hours = sunrise_hours, 
        sunrise_minutes = sunrise_minutes, 
        sunset_hours = sunset_hours, 
        sunset_minutes = sunset_minutes,
        sunset_sunrise_duration = sunset_sunrise_duration)
      
      self.send_video_to_subprocess(video_location=video_location, emotion_category="idle1")

  def clear_display_emotion(self):
    self.send_video_to_subprocess(video_location=self.subprocess_stop_video_code)

  # Given a video location, give it to the subprocess. 
  def send_video_to_subprocess(self, video_location, emotion_category = None):
    if video_location is not None and video_location != "":
      # Continue if video is none OR if the currently playing video is 
      # not equal to the new one.
      if self.subprocess_current_video is None or video_location != self.subprocess_current_video:
        # Continue if we are not attempting to stop the video OR, if we
        # are, make sure a video is actually playing. 
        if video_location != self.subprocess_stop_video_code or self.subprocess_current_video is not None:
          # Save the emotion category so we can use it to determine if
          # we can safely override the idle animation or not. (i.e. if
          # we're talking, don't give us the regular updates.)
          self.subprocess_emotion_state = emotion_category

          print("[DEBUG] Emotion Representation submitting video string: " + video_location + ".")
          try:
            # Socket interaction using multiprocessing library. 
            address = (self.subprocess_address, self.subprocess_port)
            connection = Client(address, authkey=self.subprocess_key)
            connection.send(video_location)
            connection.close()

            # Update our local knowledge of the current video. 
            if video_location == self.subprocess_stop_video_code or video_location == self.subprocess_shutdown_code:
              self.subprocess_current_video = None
            else:
              self.subprocess_current_video = video_location
          except Exception as e:
            print("[ERROR] Emotion Representation failed to play video! Exception: ")
            print(e)

  # Given the emotion category as well as optionally the sunset
  # and sunrise times for today, return a video correlated to the
  # emotion and current time.
  def derive_video_location(self, emotion_category, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration = None):
    video_location = None

    print("[DEBUG] Emotion Representation - Got Sunset, sunrise: " + str(sunset_hours) + ":" + str(sunset_minutes) + ", " + str(sunrise_hours) + ":" + str(sunrise_minutes))

    # Get the current time relative to daylight/sunset/nightlight
    # in 24 hr format. 
    current_hours = int(time.strftime("%H", time.localtime()))
    current_minutes = int(time.strftime("%M", time.localtime()))

    # Apply defaults if not provided sunset/sunrise information.
    if sunrise_hours is None: sunrise_hours = self.sunrise_default_time_hours
    if sunrise_minutes is None: sunrise_minutes = self.sunrise_default_time_minutes
    if sunset_hours is None: sunset_hours = self.sunset_default_time_hours
    if sunset_minutes is None: sunset_minutes = self.sunset_default_time_minutes
    if sunset_sunrise_duration is None: sunset_sunrise_duration = self.sunset_sunrise_duration

    # Calculate the floors/ceilings for sunset/sunrise.
    sunset_time_ceiling_hours, sunset_time_ceiling_minutes = self.adjust_time_given_duration(
      sunset_hours, sunset_minutes, sunset_sunrise_duration/2)
    sunset_time_floor_hours, sunset_time_floor_minutes = self.adjust_time_given_duration(
      sunset_hours, sunset_minutes, -sunset_sunrise_duration/2)
    sunrise_time_ceiling_hours, sunrise_time_ceiling_minutes = self.adjust_time_given_duration(
      sunrise_hours, sunrise_minutes, sunset_sunrise_duration/2)
    sunrise_time_floor_hours, sunrise_time_floor_minutes = self.adjust_time_given_duration(
      sunrise_hours, sunrise_minutes, -sunset_sunrise_duration/2)

    # For easy calculation, combine hours and minutes. 
    # Ex) 15 32 to 1532. 
    current_time = current_hours*100 + current_minutes
    sunset_ceiling = sunset_time_ceiling_hours*100 + sunset_time_ceiling_minutes
    sunset_floor = sunset_time_floor_hours*100 + sunset_time_floor_minutes
    sunrise_ceiling = sunrise_time_ceiling_hours*100 + sunrise_time_ceiling_minutes
    sunrise_floor = sunrise_time_floor_hours*100 + sunrise_time_floor_minutes

    #print("[DEBUG] Emotion Representation - Current: " + str(current_time) + " sunset: " + str(sunset_ceiling) + "/" + str(sunset_floor) + " sunrise: " + str(sunrise_ceiling) + "/" + str(sunrise_floor))

    if current_time < sunset_floor and current_time > sunrise_ceiling:
      # Daylight. 
      #print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in daylight.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_sunlight[emotion_category]
    elif current_time > sunset_ceiling or current_time < sunrise_floor:
      # Night time.
      #print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in nightlight.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_nightlight[emotion_category]
    else:
      # current time is either sunrise or sunset. 
      #print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in sunset/sunrise.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_sunset[emotion_category]
    
    # For windows, convert all slashes appropriately. OS.startfile
    # is sensitive to to this. 
    if (self.windows_platform):
      video_location = video_location.replace("/","\\")

    return video_location

  # Helper function - given a duration in minutes, adjust the
  # current minutes accordingly.  We're expecting realistic 
  # sunset/sunrise hours, so no thought is being given to 
  # things like day rollover or whatnot. 
  #
  # Duration can be positive or negative. 
  def adjust_time_given_duration(self, hours, minutes, duration):
    new_minutes = minutes + duration
    new_hours = hours
    if new_minutes > 60:
      # (Use // to get floor-rounded answer.)
      additional_hours = new_minutes//60
      new_minutes = new_minutes%60
      new_hours = new_hours + additional_hours
    elif new_minutes < 0:
      # Negate the minutes (Use // to get floor-rounded answer.)
      removed_hours = abs(new_minutes)//60 + 1
      new_minutes = 60*removed_hours + new_minutes
      new_hours = new_hours - removed_hours
    
    return new_hours, new_minutes

# Debug only.
if __name__ == "__main__":
  emotion_category = "joy"
  emotion_videos_location = "./emotion_media"
  subprocess_location = "emotion_representation_subprocess.py"

  emotion_representation = EmotionRepresentation(emotion_videos_location = emotion_videos_location, subprocess_location = subprocess_location)
  emotion_representation.start_display_emotion(emotion_category=emotion_category)
  time.sleep(5)
  emotion_representation.stop_display_emotion()