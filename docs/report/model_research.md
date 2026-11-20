# Model research: rest vs. contraction from single-channel sEMG

Scope: candidate classifiers for our frozen input (4 time-domain features per 200 ms window, divided by rest
level, log + standardised), one subject, one muscle, ~10 electrode placements, sklearn only, live at 10 Hz.
All sources below were opened (PubMed/Europe PMC abstracts, full text where noted). Date of search: 2026-11-19.

**Caveat:** most classifier comparisons in the literature are **multi-class, multi-channel forearm** studies
(prosthesis control), not binary single-channel. Their numbers show *relative robustness*, not what we will get.

## 1. Candidate table

| # | Approach | How it works (1 line) | Evidence (opened) | Fit to our constraints | Main risk |
|---|---|---|---|---|---|
| A | **Double threshold / hysteresis** (= our `ThresholdModel`) | "on" above a high threshold, "off" below a low one; optionally require m of n samples | Bonato, D'Alessio, Knaflitz 1998, *A statistical method for the measurement of muscle activation intervals from surface myoelectric signal during gait*, IEEE TBME 45(3):287-299, doi:10.1109/10.661154. Abstract: "bias of the estimates of the on-off transitions is smaller than 10 ms, the standard deviation may be kept lower than 15 ms, and the percentage of erroneous patterns is below 5%" (simulation + gait, onset timing, not window accuracy). Also: "for a fixed value of the Pfa, they yield higher detection probability" than single thresholds. | No training, 1 feature (RMS ratio), trivially explainable and live. Already implemented. | Thresholds in "× rest" are fixed by hand; weak/light contractions or fatigue can fall between them. |
| B | **Single threshold, mean + k·SD of baseline, min duration** | onset when signal stays > baseline mean + k·SD for ≥ t ms | Hodges & Bui 1996, *A comparison of computer-based methods for the determination of onset of muscle contraction using electromyography*, Electroencephalogr Clin Neurophysiol 101(6):511-519, doi:10.1016/s0013-4694(96)95190-5. Compared 27 combos (low-pass 10/50/500 Hz, k = 1/2/3 SD, 20/50/100 ms); "onset values selected by the majority of the parameter combinations deviated significantly from the visually derived onset values". Best combo: not in abstract (not verified). | Same as A. Useful offline to *check* where contractions really start (TRIM_S question). | Parameter-sensitive (that is the paper's main finding). |
| C | **LDA** (linear discriminant analysis) | Gaussian classes with shared covariance → linear boundary | Kaufmann, Englehart, Platzner 2010, *Fluctuating EMG signals: investigating long-term effects of pattern matching algorithms*, IEEE EMBC 2010:6357-60, doi:10.1109/IEMBS.2010.5627288 (full text PDF read). 21 days, 121 trials, MAV/ZC/SSC/WL, 10 hand movements. Table I test error, trained on first 5 / recent 5 / all preceding trials: **LDA 21.27 % / 17.63 % / 17.54 %**; text: "Accuracy for LDA drops only by 3.6% when not being trained recurrently" (= first 5 vs recent 5: 21.27 − 17.63 = 3.64); "While LDA is robust when not being trained recurrently, SVMs and MLPs excel for the other benchmarks." Young, Hargrove, Kuiken 2011, IEEE TBME 58(9):2537-44, doi:10.1109/TBME.2011.2159216 (PMC4234036): LDA on Hudgins TD features; the MLP "did not generalize as well as the LDA at any of the shift locations" (shift error numbers only in figures, not verified). | Linear, 4 weights, trains in ms, `sklearn.discriminant_analysis`. Very good fit. | Assumes Gaussian classes with equal covariance; rest windows have much smaller variance than contraction windows. |
| D | **Logistic regression** (our default `MLModel("logreg")`) | linear boundary on log-features, outputs P(contraction) | EMG-specific comparison for our setting: **not found**. Same linear decision family as LDA (C), so C's robustness argument is the closest evidence (inference, not a measured result). Imbalance handling: see section 4b. | Best fit: explainable (weights per feature), `class_weight` built in, probabilities allow hysteresis. | No direct EMG evidence; a linear boundary may miss non-linear fatigue effects. |
| E | **SVM (RBF)** | maximum-margin boundary, kernel for non-linearity | Oskoei & Hu 2008, *Support vector machine-based classification scheme for myoelectric control applied to upper limb*, IEEE TBME 55(8):1956-65, doi:10.1109/TBME.2008.919734: compared with LDA and MLP, "exceptional accuracy, robust performance, and low computational load" (no numbers in abstract). Kaufmann 2010: **SVM 27.35 % error trained on first 5 trials vs 10.34 % on all preceding** (best when retrained, worst-but-one when not). | sklearn, fast enough live. Less explainable. | Degrades most when the data drift (our case: unseen placement, no retraining). |
| F | **kNN** | majority label of the k nearest training windows | Kaufmann 2010: **kNN 27.38 % vs 16.03 %** (first 5 vs all preceding trials). | sklearn, but stores all windows; not a "model" to explain. | Sensitive to feature-space shift from re-placement. |
| G | **Decision tree / random forest** (our comparison `MLModel("forest")`) | many trees vote on thresholds of single features | Kaufmann 2010 (single decision tree): **DT 31.19 % vs 13.28 %** — largest degradation when not retrained. Random forest in a comparable cross-session binary setting: **not found**. (Shinde et al. 2026, J Electr Bioimpedance, doi:10.2478/joeb-2026-0016, single MyoWare + Arduino, 3 gestures, LOSO live accuracy RF 68.7 %, best of their 5 models — different task, cross-subject.) | sklearn, feature importances explainable-ish. | Overfits per-placement detail with ~10 placements. |
| H | **Temporal smoothing: majority vote / HMM** (post-processing, not a classifier) | smooth the stream of window decisions over time | Englehart & Hudgins 2003, *A robust, real-time control scheme for multifunction myoelectric control*, IEEE TBME 50(7):848-54, doi:10.1109/TBME.2003.813539: continuous decision stream without segmentation, "substantial gains in classifier accuracy and response time" (majority-vote post-processing: from full text, not verified by us; numbers not in abstract). Chan & Englehart 2005, IEEE TBME 52(1):121-4, doi:10.1109/TBME.2004.836492: HMM "capable of higher classification accuracy than previous methods based upon multilayer perceptrons" (no number in abstract). | Our `Smoother` already does majority vote; works on top of any of A-G. A 2-state HMM is ~20 lines of numpy. | Adds latency (k × 100 ms); HMM transition probabilities must not be tuned on test sessions. |

Not found / not verified: Gaussian Naive Bayes for EMG activity detection with cross-session numbers (searched, nothing usable);
Hargrove, Englehart, Hudgins 2006 EMBC (doi:10.1109/iembs.2006.260681) states electrode-displacement effects "can be mitigated
by using a training set of data which consists of patterns detected over a range of plausible displacement locations" (no numbers in abstract).
→ For us: train on **all** train placements, which leave-one-placement-out already does.

## 2. Ranked recommendation (top 3)

1. **Logistic regression (D), with LDA (C) as a cheap cross-check.** Linear models degraded least across days in the
   only multi-classifier drift study we could read (Kaufmann 2010, first 5 vs recent 5 trials: LDA 3.6 points vs 8.6–14.6 for the others) and generalised
   better than an MLP under electrode shift (Young 2011). Explainable in an exam (one weight per feature), trains in < 1 s,
   `class_weight` and probabilities built in. LDA costs one line in `evaluate.py`, so report both.
2. **Double-threshold / hysteresis model (A).** No training, physiologically motivated, strong onset-timing results
   (Bonato 1998), and our fallback when ML is weak. It is also the "threshold floor" the course asks us to beat.
3. **Random forest (G) — only as the non-linear comparison.** Keep it in `evaluate.py` to show *whether* non-linearity helps on
   real data; the literature (Kaufmann 2010, DT/SVM/kNN) predicts that flexible models lose most on unseen sessions.
   Pick it only if leave-one-placement-out on **train** sessions clearly favours it.

Apply **majority-vote smoothing (H)** on top of whichever wins (already in `Smoother`); report window-level and smoothed scores.
Drop SVM and kNN: no explainability gain, worst drift behaviour in Kaufmann 2010.

## 3. Evidence for TRIM_S and class imbalance

### (a) How long after the cue does EMG start/stop? Is TRIM_S = 1.5 s reasonable?

- **Onset after a visual cue ≈ 0.3–0.4 s.** Xiao et al. 2024, *Relationship between fear-avoidance beliefs and reaction time
  changes prior to and following exercise-induced muscle fatigue in chronic low back pain*, doi:10.1155/2024/9982411
  (PMC10838204, Table 2 read): premotor time (visual cue → EMG onset, deltoid) median **0.333 s (IQR 0.301–0.390)** before
  fatigue, **0.386 s (0.328–0.444)** after fatigue; electromechanical delay 0.025 s. (Patients with low back pain, deltoid,
  not biceps → order of magnitude only.)
- **Fatigue makes onset later** (same table: +~0.05 s), so fatigued samples need a little more margin, not less.
- **Slow ramps can take seconds.** Basile et al. 2024, J Neurophysiol 132(6):1670-9, doi:10.1152/jn.00330.2024: biceps,
  visual "GO" cue, slow condition "25% MVC/s" to a 50 % MVC target → **≈ 2 s ramp** (our arithmetic from the abstract).
- **Offset (contract → rest) for the biceps: not verified.** Found only a finger-muscle study (Suzuki et al. 2015,
  doi:10.1152/jn.00489.2014) without an offset-latency number in the abstract.

**Conclusion:** 1.5 s is ~4× the typical reaction time and also covers a moderately slow ramp; it is defensible, possibly
generous (it keeps 5 of 8 s per phase). Verify on our **train** data: run an onset detector (A or B, e.g. baseline mean + 3 SD)
on each sample and plot onset/offset delay vs cue. If 95 % of delays are < 1 s, TRIM_S = 1.0 s is justified.
Hodges & Bui 1996 warn that detector parameters change the onset estimate, so state the detector used.

### (b) 1:2 class imbalance (8 s contraction vs 16 s rest; clean windows: 5 s vs 10 s)

- **Resampling harms logistic regression.** van den Goorbergh, van Smeden, Timmerman, Van Calster 2022, *The harm of class
  imbalance corrections for risk prediction models: illustration and simulation using logistic regression*, JAMIA
  29(9):1525-34, doi:10.1093/jamia/ocac093 (PMC9382395): undersampling, oversampling and SMOTE "yielded poorly calibrated
  models: the probability to belong to the minority class was strongly overestimated"; they "did not result in higher areas
  under the ROC curve"; better sensitivity/specificity balance, but "similar results were obtained by shifting the probability
  threshold instead". Conclusion: "Outcome imbalance is not a problem in itself, imbalance correction may even worsen model
  performance." (Medical risk models with much stronger imbalance; class weighting itself was not one of their 4 methods →
  not verified for weights.)
- **sklearn class weights:** "The “balanced” mode uses the values of y to automatically adjust weights inversely proportional
  to class frequencies in the input data as n_samples / (n_classes * np.bincount(y))." For us: rest 0.75, contraction 1.5.
- **Metric:** balanced accuracy = "the average of recall obtained on each class" (sklearn docs) — chance stays 50 % at 1:2.

**Recommendation:** 1:2 is mild. **No resampling** (no SMOTE). Use `class_weight="balanced"` (one argument, no new data) *or*
keep weights off and tune the decision threshold on train placements — pick one, choose it on train sessions only, and always
report balanced accuracy plus the confusion matrix. Note in DECISIONS.md that the course PDF's "about the same amount" is
met at the loss level (weights), not in the raw recording.
