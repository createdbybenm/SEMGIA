**DRAFT – Ben rewrites the reasons in his own words before Report 1.**

# Decisions

For every part: what we chose, the reason, and what we still do not understand.
All choices are made with the training sessions only. A session is one electrode placement (E01, E02, ...).
The test sessions are listed in `TEST_PLACEMENTS` in `semgia/config.py` and are opened once, at the end
(`python scripts/evaluate.py --final`).

## 7 Features

What we chose: four numbers per 200 ms window (new window every 100 ms): RMS, mean absolute value (MAV),
waveform length (WL) and zero crossings (ZC). Each one is divided by the rest level, so 1.0 means "like rest".
Right now the rest level is the first rest phase of the same sample. The plan is one calibration per placement. Windows closer than 1.5 s to a cue change are not used for training (TRIM_S).
Filtering is analog (20-447 Hz band-pass and 60 Hz notch), so in software we only subtract the mean
of each window to remove the ESP32 offset of about 2048.

Why (reason): RMS, MAV and WL measure the size of the signal, and in a contraction they go up several
times. ZC is a rough frequency measure, and the frequency drops with fatigue, so it should help with the
fatigued samples. Dividing by rest removes the gain that changes every time the electrodes go on again.
The 1.5 s trim is about four times the normal reaction time after a visual cue: Xiao et al. 2024 measured
a median of 0.333 s from cue to EMG onset, and 0.386 s after fatigue. So the clean windows should really be
steady rest or steady contraction. We will check this by eye on our training data with
`scripts/first_look.py`.

Not understood yet: whether ZC adds anything on our sensor, or if RMS alone is enough. We also do not
know yet how long the biceps needs to relax after the cue, because we found no number for the offset.

Source: Xiao et al. 2024 (see Sources).

## 8 Model

What we chose: not decided yet. We compare three options on the same four features:
logistic regression (our default), LDA and a random forest. A threshold on RMS (3x rest on, 2x rest off)
is the floor every model has to beat. A majority vote over the last 5 windows smooths the output.

Why (reason): We need a model that still works when the electrodes are put on again. In Kaufmann et al.
2010 (21 days of EMG), LDA lost only 3.6 percentage points when it was not retrained (first 5 vs. recent
5 trials), the other models lost 8.6 to 14.6 points. Young et al. 2011 found that LDA generalised better
than a neural network when the electrodes were shifted. Logistic regression is also linear, and we can
explain it with one weight per feature. The random forest is only there to show if a non-linear model helps
on our data. We score with leave-one-placement-out on the training sessions, and we always report accuracy
and balanced accuracy next to two floors: chance (share of the bigger class, about 67 % because rest is
16 s of 24 s) and the threshold model. Rest is twice as long as contraction, so we use class weights
(LDA: equal priors) and do not resample. Van den Goorbergh et al. 2022 showed that resampling made
logistic regression badly calibrated and did not improve the AUC. The final choice waits for real data.

Not understood yet: how LDA draws the border when rest windows vary much less than contraction
windows, since LDA assumes the same spread for both classes. On our mock data it already missed part of
a fatigued sample. We also do not know if smoothing helps overall, because it adds about 0.2 s of delay at
every cue change.

Source: Kaufmann et al. 2010, Young et al. 2011, van den Goorbergh et al. 2022 (see Sources).

## 9 Route

What we chose: the model runs in our own Python software on the laptop (`scripts/record.py` / `import_web.py`
replay the signal through the same filter, features and model as training). Each recording is saved locally first
(`data/raw/sample_NNN/`), then uploaded to Microsoft Azure: the raw signal as blobs (container `signals`), the
metadata as one row in the table `samples`, and the model output per 100 ms window in the table `predictions`.
A small Streamlit dashboard on Azure App Service (free F1 plan) reads them back, like a doctor opening a patient
record. Everything sits in the region belgiumcentral (EU), with no public access. Evidence: `semgia/storage.py`,
`docs/azure_setup.md`, `figures/azure_record.png` (one saved record with its metadata).

Why (reason): our Python code on the laptop already does everything: filter, features and model.
If we moved the model to the ESP32 we would have to write it a second time, and the two versions could
give different answers. We save every recording on the laptop first, so if the Wi-Fi fails we lose
nothing and upload it later. We picked Azure because our student account is free, we set a budget
alert so it cannot cost us money, and we can delete one person's recording everywhere with one command.

Not understood yet: whether the free dashboard plan is fast enough for the live demo (it sleeps when
nobody uses it and the first load takes about a minute), and how the ESP32 itself could send the
record to Azure if one day we wanted to work without the laptop.

## Sources
- Kaufmann P, Englehart K, Platzner M. Fluctuating EMG signals: investigating long-term effects of pattern
  matching algorithms. IEEE EMBC 2010:6357-60. doi:10.1109/IEMBS.2010.5627288
- Young AJ, Hargrove LJ, Kuiken TA. IEEE TBME 2011;58(9):2537-44. doi:10.1109/TBME.2011.2159216
- Xiao et al. 2024. Relationship between fear-avoidance beliefs and reaction time changes prior to and
  following exercise-induced muscle fatigue in chronic low back pain. doi:10.1155/2024/9982411
- van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. The harm of class imbalance corrections
  for risk prediction models. JAMIA 2022;29(9):1525-34. doi:10.1093/jamia/ocac093
- Details and quotes: `docs/report/model_research.md`.
