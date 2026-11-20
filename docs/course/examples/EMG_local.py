# EMG_local.py: the Colab as one plain Python script, for a laptop without Colab.
# Needs: Python 3, numpy, scipy, matplotlib (pip install numpy scipy matplotlib) and git.
# Run from the folder where you want the dataset folder to be:  python3 EMG_local.py
# The code lines are the same as in EMG_Colab.ipynb. Only the first step differs: Colab runs
# "!git clone ..." as a shell command. Plain Python calls git through subprocess instead.
import os                                          # tools for files and folders
import subprocess

# ---- Step 1: copy the 445 recordings from GitHub into this folder (only once)
if not os.path.exists("MuscleTracker-Hand-Movement"):   # only download once
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/RQ-FA/MuscleTracker-Hand-Movement"], check=True)
print("Dataset ready.")
print("This script runs in the folder:", os.getcwd())   # the dataset folder sits inside it

# ---- Step 2: the tools, the folder, and the one number everything depends on
import numpy as np                   # arrays of numbers
import matplotlib.pyplot as plt      # plots
import scipy as sp                   # the FFT (Step 7)

DATA = "MuscleTracker-Hand-Movement/Data/Raw/Biopac"   # where the files are
FS = 1000                                              # Hz, from the paper (not computed)

files = sorted(os.listdir(DATA))     # every file name in the folder
print("Number of recordings:", len(files))
print("First five:", files[:5])

# ---- Step 3: write the file name for subject 10, repetition 1, movement 2 (flexion)
fname = "10_1_2.txt"   # pattern: subject_repetition_movement.txt
assert fname in files, f"'{fname}' does not exist. Pattern: subject_repetition_movement.txt"
print("Correct:", fname)

# ---- Step 4: load the file. One row per sample; two columns = the two channels.
x = np.loadtxt(os.path.join(DATA, fname), delimiter=",")   # read the numbers into an array
N = len(x)                                                 # number of samples
print("Rows x columns:", x.shape)
print("Samples:", N)
print("Duration:", N / FS, "seconds")    # samples / (samples per second) = seconds

# ---- Step 5: time axis and plot. Recipe: t = n / Fs
t = np.arange(N) / FS            # 0, 1, 2, ... N-1  ->  seconds
plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(t, x[:, 0])             # all rows, column 0 = channel 1
plt.ylabel("ch1 (file units)")
plt.title("Subject 10 - flexion (m2) - raw surface EMG")
plt.subplot(2, 1, 2)
plt.plot(t, x[:, 1])             # channel 2
plt.ylabel("ch2 (file units)")
plt.xlabel("Time (s)")
plt.tight_layout()
plt.show()

# ---- Step 5b: is it muscle or just noise? Compare with a REST file, same scale.
x_rest = np.loadtxt(os.path.join(DATA, "10_1_5.txt"), delimiter=",")   # subject 10, rest (m5)
top = max(abs(x[:, 0]).max(), abs(x_rest[:, 0]).max())                 # one y-scale for both
plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(t, x[:, 0]);  plt.ylim(-top, top)
plt.ylabel("flexion (file units)");  plt.title("Same scale: flexion (top) vs rest (bottom)")
plt.subplot(2, 1, 2)
plt.plot(np.arange(len(x_rest)) / FS, x_rest[:, 0]);  plt.ylim(-top, top)
plt.ylabel("rest (file units)");  plt.xlabel("Time (s)")
plt.tight_layout()
plt.show()

# ---- Step 6: same movement, three people. Change SUBJECT_3 to any number 1..30 except 10 and 11.
SUBJECT_3 = 21
plt.figure(figsize=(10, 6))
for i, s in enumerate([10, 11, SUBJECT_3]):                              # i = 0,1,2   s = subject
    xi = np.loadtxt(os.path.join(DATA, f"{s}_1_2.txt"), delimiter=",")   # repetition 1, flexion
    plt.subplot(3, 1, i + 1)
    plt.plot(np.arange(len(xi)) / FS, xi[:, 0])
    plt.ylabel(f"subject {s}")
plt.xlabel("Time (s)")
plt.suptitle("Flexion (m2), channel 1 - three different people")
plt.tight_layout()
plt.show()

# ---- Step 7: the spectrum. Recipe: FFT -> magnitude -> frequency axis f = m * Fs / N -> first half
sig = x[:, 0]                          # channel 1 of the flexion file
Xm = np.abs(sp.fft.fft(sig)) / N       # how much of each frequency (magnitude, normalised)
f = np.arange(N) * FS / N              # bin number -> Hz
half = N // 2                          # above Fs/2 the spectrum only mirrors itself
plt.figure(figsize=(10, 4))
plt.plot(f[:half], Xm[:half])
plt.xlabel("Frequency (Hz)");  plt.ylabel("Amplitude (file units)")
plt.title("Spectrum of raw surface EMG - flexion, ch1")
plt.show()

# ---- Step 8: choose the band from the literature, then let the numbers CHECK it.
# Sources: 10-500 Hz (dataset paper), 20-450 Hz (this course), 20-500 Hz (McManus 2020)
BW_LOW = 20     # lower edge, Hz
BW_HIGH = 450   # upper edge, Hz
power = Xm[:half] ** 2
inside = (f[:half] >= BW_LOW) & (f[:half] <= BW_HIGH)        # True where the bin is in your band
print(f"Your band: {BW_LOW}-{BW_HIGH} Hz")
print(f"Check: {power[inside].sum() / power.sum():.1%} of this file's power is inside it.")
print(f"Nyquist: sample at least 2 x {BW_HIGH} = {2 * BW_HIGH} Hz. BIOPAC used {FS} Hz (margin).")
