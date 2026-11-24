# SEMGIA glossary

Words for one patient, one muscle, single-channel sEMG, classified as contraction or rest. Use these terms in code,
docs and commits. Where the course uses another word, it is listed under _Course word_.

## Recording

**Patient**:
The one person whose muscle the model is built for (pseudonym `P002`). Recordings of anyone else are rejected.
_Avoid_: user, test person

**Placement**:
One application of the electrodes on the skin, numbered `E01`, `E02`, …. A new number every time the electrodes are re-applied.
_Course word_: session · _Avoid_: setup, run

**Sample**:
One continuous 24 s recording within a placement: rest 8 s, contract 8 s, rest 8 s (`sample_NNN`).
_Course word_: recording; it holds exactly one trial · _Avoid_: trial, take, measurement

**Trial**:
One cue → action → rest cycle. For us one sample = one trial; the word is only used when quoting the course.

**Cue**:
The on-screen instruction (REST / CONTRACT) shown to the patient during a sample, driven by the timer.

**Label**:
Rest (0) or contraction (1) for one reading, taken from the timer, never from the signal or the person.
_Avoid_: ground truth, annotation

**Effort**:
How hard the patient was asked to contract in a sample: light, medium or strong.

**Condition**:
Whether the muscle was fresh or fatigued when the sample was recorded.

**Operator**:
The team member running the recording (pseudonym `OP01`, …).

## Signal and features

**sEMG**:
Surface electromyography: the muscle's electrical activity measured through electrodes on the skin.

**Window**:
200 ms of signal; a new window starts every 100 ms. The model gives one prediction per window.

**Clean window**:
A window at least 1.5 s away from every label change and from the start and end of the sample.
Only clean windows are used for training.
_Avoid_: valid window, steady-state window

**Features**:
The four numbers computed per window: RMS (root mean square), MAV (mean absolute value), WL (waveform length),
ZC (zero crossings).

**Rest baseline**:
The rest level of the features, used to divide every feature so 1.0 means "like rest".
Today it is the clean part of each sample's first rest phase.
_Avoid_: offset, zero level

**Calibration**:
A rest + maximum contraction recorded once per placement, scaling signals to 0 (rest) … 1 (maximum).
Agreed as the target but not built; the rest baseline is used instead.
_Avoid_: using "calibration" for the per-sample rest baseline

**MVC**:
Maximum voluntary contraction: the strongest contraction the patient can hold.

## Evaluation

**Train set / test set**:
Placements used to choose features and models (train) and placements opened once at the end to report the score
(test). Each placement is in exactly one of them.
_Avoid_: validation set (for the test placements)

**Leave-one-placement-out (LOPO)**:
Train on all train placements but one, score on the one left out, rotate, average. Picks the model.
_Course word_: leave-one-session-out

**Balanced accuracy**:
The mean of the accuracy on rest windows and the accuracy on contraction windows.

**Floor**:
A score any useful model must beat: the chance floor (share of the majority class) and the threshold floor
(the untrained threshold model).
