# Decisions

Every choice below was made with the training sessions only (E02 to E05). The test session E06 is opened once, at the
end (`python scripts/evaluate.py --final`). A session is one electrode placement.

## 7 Features

Chose: four numbers per 200 ms window, with a new window every 100 ms: RMS, mean absolute value (MAV), waveform length
(WL) and zero crossings (ZC). Each one is divided by the rest level of the recording, so 1.0 means "like rest". For
training we only use windows that are at least 1.5 s away from a cue change.

Reason: RMS, MAV and WL measure how big the signal is, and in our recordings they go up several times when the
hamstrings contract. ZC is a rough measure of frequency, which drops with fatigue, so it should help on the fatigued
recordings. Dividing by the rest level removes the gain change that comes with every new electrode placement. The
1.5 s gap is about four times the normal reaction time after a cue (median 0.333 s in Xiao et al. 2024).

Not understood yet: whether ZC adds anything on our sensor or whether RMS alone is enough, and how long the
hamstrings need to fully relax after the rest cue.

## 8 Model

Chose: not decided yet. We compare three models on the same four features: logistic regression, linear discriminant
analysis (LDA) and a random forest. A threshold on RMS (above 3 times rest is contraction, below 2 times rest is rest)
is the floor every model has to beat, and chance is 67 % because rest is 16 s of every 24 s. In our first
leave-one-session-out run on the training sessions, logistic regression reached 0.90 on clean windows and 0.85 on all
windows, LDA 0.90 and 0.85, the random forest 0.88 and 0.83, and the threshold 0.80 and 0.78. We take the one that is
best on the training sessions and test it once on E06.

Reason: we have only 23 usable training recordings, so a simple linear model should transfer best to a new electrode
placement. Kaufmann et al. 2010 and Young et al. 2011 found that LDA stayed more stable than other models over days and
with shifted electrodes. The random forest shows whether a non-linear border helps at all. Rest is twice as long as
contraction, so we use class weights and do not resample (van den Goorbergh et al. 2022).

Not understood yet: how LDA draws the border when the rest windows vary much less than the contraction windows, and
whether smoothing the output over 5 windows helps more than the delay it adds at every cue change.

## 9 Route

Chose: the model runs in our own Python software on the laptop, which gets the signal from the ESP32 web page. Each
recording is saved locally first and then uploaded with its metadata to Microsoft Azure (Blob Storage for the signal,
Table Storage for metadata and predictions), and a small dashboard on Azure App Service shows the records.

Reason: the features and the models are already in Python, and the laptop receives the data anyway. Saving locally
first means a network problem never loses a recording, and Azure has a free student plan.

Not understood yet: how the ESP32 page could upload a record to Azure directly without the import step on the laptop,
and whether the model would be fast enough as TinyML on the ESP32.

## Sources
- Kaufmann P, Englehart K, Platzner M. Fluctuating EMG signals: investigating long-term effects of pattern matching
  algorithms. IEEE EMBC 2010:6357-60. doi:10.1109/IEMBS.2010.5627288
- Young AJ, Hargrove LJ, Kuiken TA. The effects of electrode size and orientation on the sensitivity of myoelectric
  pattern recognition systems to electrode shift. IEEE TBME 2011;58(9):2537-44. doi:10.1109/TBME.2011.2159216
- Xiao et al. 2024. Relationship between fear-avoidance beliefs and reaction time changes prior to and following
  exercise-induced muscle fatigue in chronic low back pain. doi:10.1155/2024/9982411
- van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. The harm of class imbalance corrections for risk
  prediction models. JAMIA 2022;29(9):1525-34. doi:10.1093/jamia/ocac093
- Full train results: `docs/report/results_train.md`.
