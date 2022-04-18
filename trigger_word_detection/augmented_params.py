#
# augmented_params.py
#
# Configurable relating to the creation and usage of augmented datasets
# in order to regularize an existing model.

checkpoints_folder = "./model_checkpoints"
raw_data_folder = "./raw_data"

Tx = 5511 # The number of time steps input to the model from the spectrogram
n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
Ty = 1375 # The number of time steps in the output of our model

# Training parameters
validation_split = 0.2
batch_size = 32

# Creation of the augmented dataset. This is not saved to file, but
# generated every single augmentation loop and used immediately. 
dataset_size = 9000
min_positives = 0
max_positives = 4
min_negatives = 0
max_negatives = 4

# Audio Augmentation bounds. Initial settings were taken directly from
# the Maestro dataset paper (Hawthorne et al. 2019). Sampling options
# are "linear" and "log".
#pitch_shift = (-0.1, 0.1)
pitch_shift = (-3.0, 3.0) # We REALLY want different pitches. 
pitch_shift_sampling = "linear"
contrast = (0.0, 100.0)
contrast_sampling = "linear"
equalizer_1 = (32.0, 4096.0)
equalizer_1_sampling = "linear"
equalizer_2 = (32.0, 4096.0)
equalizer_2_sampling = "linear"
reverb = (0.0, 10.0)
reverb_sampling = "linear"

# Equalizer static variables. 
equalizer_q = 1.0
equalizer_gain = 1.0