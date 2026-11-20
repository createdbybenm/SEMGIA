# The professor's example repo (summary)

Source: https://github.com/MahdiTec/emg-data-stage-example (read 2026-11-19). All numbers there are invented and the
raw files are empty. **Copy the structure and the style, never the values or the wording**: "a report that repeats
the example is returned".

## File tree
```
README.md            team table + the six parts, each with an "Evidence:" line naming files/columns
PROTOCOL.md          numbered method (sensor/site, posture, task, trial, recording, cue, session, settings,
                     filters, when to repeat, consent) + "We read the method and we agree" (1 line per member)
DECISIONS.md         7 Features / 8 Model / 9 Route: Chose · Reason, in our own words · Not understood yet · Source
QUALITY-REPORT.md    rule (written before any score) + table File | Session | Trials | Rejected | Reason
                     + Totals, Noise (rest vs movement size), Outliers
DATA-DICTIONARY.md   one row per metadata column: meaning + unit/allowed values
CHANGELOG.md         one entry per version with a "Why"
ai-tools/            M01.png … + README
rationale/           M01.md … (~100 words, 1 source) + README
code/                record_emg.ino, check_quality.py (each file starts with 1 line: what it does + who wrote it)
cue/                 cue-video.mp4 (+ the pptx it was made from)
figures/             placement_S01.jpg … (one per session, no faces), one_recording_marked.png, two_features.png
data/metadata.csv    one row per recording
data/raw/P01_S01_R01.csv …   columns time_ms,emg_adc
```
Versions are shown as GitHub Releases ("First version", "Report 1").

## Example `data/metadata.csv` columns
`file_name, participant, session, date, recording, trials, rest_s, warning_s, move_s, between_s, fs_hz, muscle, side,
electrodes, electrode_type, electrode_distance_cm, skin_preparation, sensor_model, gain, adc_bits, cue, set,
trials_rejected, notes`. The PDF requires at least: `session, date, rest_s, warning_s, move_s, between_s,
electrode_type, electrode_distance_cm, skin_preparation, sensor_model, gain, fs_hz, adc_bits, set`.

## Style rules taken from it
- Write numbers, not adjectives. Give seconds, counts and file names. Use codes, never names.
- Every README part ends with **Evidence:** pointing to files or columns.
- Part 6 states the limit: one person, one movement; no shuffling of windows of one recording between train and test.
- PROTOCOL.md must be enough for an outsider to repeat the recording without asking.
- The rejection rule is written **before** looking at any score.
