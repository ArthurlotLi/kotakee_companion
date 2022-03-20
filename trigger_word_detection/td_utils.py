import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
from pydub import AudioSegment

# Calculate and plot spectrogram for a wav audio file
def graph_spectrogram(wav_file):
    rate, data = get_wav_info(wav_file)
    nfft = 200 # Length of each window segment
    fs = 8000 # Sampling frequencies
    noverlap = 120 # Overlap between windows
    nchannels = data.ndim
    if nchannels == 1:
        pxx, freqs, bins, im = plt.specgram(data, nfft, fs, noverlap = noverlap)
    elif nchannels == 2:
        pxx, freqs, bins, im = plt.specgram(data[:,0], nfft, fs, noverlap = noverlap)
    return pxx

# Load a wav file
def get_wav_info(wav_file):
    rate, data = wavfile.read(wav_file)
    return rate, data

# Used to standardize volume of audio clip
def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

# Load raw audio files for speech synthesis
def load_raw_audio(raw_data_folder = "./raw_data"):
    totalFiles = 0

    activates = []
    backgrounds = []
    negatives = []
    for filename in os.listdir(raw_data_folder + "/activates"):
        if filename.endswith("wav"):
            activate = AudioSegment.from_wav(raw_data_folder + "/activates/"+filename)
            activates.append(activate)

            totalFiles = totalFiles + 1
            print("   Loaded WAV file " + str(totalFiles) + " " + raw_data_folder + "/activates/"+filename)
    for filename in os.listdir(raw_data_folder + "/backgrounds"):
        if filename.endswith("wav"):
            background = AudioSegment.from_wav(raw_data_folder + "/backgrounds/"+filename)
            backgrounds.append(background)

            totalFiles = totalFiles + 1
            print("   Loaded WAV file " + str(totalFiles) + " " + raw_data_folder + "/backgrounds/"+filename)
    for filename in os.listdir(raw_data_folder + "/negatives"):
        if filename.endswith("wav"):
            negative = AudioSegment.from_wav(raw_data_folder + "/negatives/"+filename)
            negatives.append(negative)

            totalFiles = totalFiles + 1
            print("   Loaded WAV file " + str(totalFiles) + " " + raw_data_folder + "/negatives/"+filename)
        elif filename.endswith("ogg"):
            # Support oggs downloaded from lingualibre.org.
            negative = AudioSegment.from_ogg(raw_data_folder + "/negatives/"+filename)
            negatives.append(negative)

            totalFiles = totalFiles + 1
            print("   Loaded OGG file " + str(totalFiles) + " " + raw_data_folder + "/negatives/"+filename)
    return activates, negatives, backgrounds