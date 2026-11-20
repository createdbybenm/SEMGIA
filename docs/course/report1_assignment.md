# Report 1: the assignment (transcript of `report1_assignment.pdf`)

> Faithful transcript of "Dataset Evidence M2A 16 Nov". **This is the authoritative assignment.** If anything here
> differs from the slides, this wins. Only the layout changed; the wording is the professor's.

M6 MACHINE LEARNING AND IOT APPS · REPORT 1 · NOT GRADED (the grade comes from the final delivery)

## Present your data stage, and decide what comes next
**Due Saturday 21 November, 23:59.** Send one link per group to your private GitHub repository, with the professor
added as collaborator.

You measure one person and one movement. You build a model for that person and test it on the same person with new
electrodes. The final goal: the model is right more than 75 % of the time on sessions it never saw. At the end the
model runs, and each measurement is saved with its metadata in a cloud service, the way a doctor saves the record of a
patient.

The examples below are invented and short on purpose. Choose your own movement and your own seconds. **A report that
repeats the example is returned.** The complete example is here: https://github.com/MahdiTec/emg-data-stage-example
(summary: [example_repo.md](example_repo.md)).

## A. Present what you did, in README.md
| Part | Example of a short answer (invented) |
|---|---|
| 1 Data acquisition | 24 recordings, 120 trials, 6 sessions, 1 person. Gel electrodes 2 cm apart on the forearm. 1000 samples per second. |
| 2 Task | Close the right hand into a fist and hold it. Two classes: movement and rest. |
| 3 Trial and cue timing | Rest 3 s, warning 1 s, movement 4 s, rest 2 s. Five trials in one recording. The person follows our cue video. |
| 4 Sessions | 6 sessions on 3 days. New electrodes in every session. |
| 5 Cleaning | A band-pass filter and a notch filter at 60 Hz. We reject a trial if a sample hits the limit of the converter, or if samples are missing. 7 of 120 rejected. |
| 6 Fair split | Sessions 1 to 4 train the model. Sessions 5 and 6 test it. No session is in both. |

If you recorded movement and rest in separate files, one file is one trial. If your sensor gives a smoothed signal,
say so. **Keep about the same amount of movement and of rest.**

## B. Decide what comes next, in DECISIONS.md
For parts 7, 8 and 9 write three short lines.
1. What we, or our AI tool, chose.
2. The reason, in our own words.
3. What we still do not understand.

"Not decided yet" is a good answer if you name the options you compare. "We do not understand this yet" is also a
good answer. It tells us what to teach next. **Choose with the training sessions only, and open the test sessions
once, at the end.**

| Part | Example of a short answer (invented) |
|---|---|
| 7 Features | Chose: two numbers per short window that measure the size of the signal. Reason: in our plot, movement and rest sit apart. Not understood yet: would a feature about frequency add anything? |
| 8 Model | Not decided yet. We compare three kinds of model, from the simplest to the most flexible. Our AI tool suggested the middle one. Not understood yet: how it draws the border between the classes. |
| 9 Route | Chose: the model runs on our ESP32. Each measurement is saved with its metadata in a cloud service. Reason: it works without a computer. Not understood yet: how the board sends the record. |

For part 9: the model can run in your own software on a computer, or as TinyML on your ESP32 or Arduino. The cloud
service can be Microsoft Azure or any other. ThingSpeak is accepted if no account works for your group.

## C. Each of you, alone
One file in `rationale/`, about 100 words, in your own words: one choice of your group that you support or doubt,
why, and one source you found. One screenshot in `ai-tools/` of the AI tool you use, open on this project, with one
question you asked it. Every member uses an AI tool. Any free tool counts. Name both files with your member code.

## Checklist: your repository holds
- [ ] `README.md`: the six parts, and a team table with member code, GitHub user, role and AI tool
- [ ] `PROTOCOL.md`: your method, the type, order and limits of each filter with their source, and one line per member: "I read the method and I agree"
- [ ] `data/raw/`: every recording, untouched
- [ ] `data/metadata.csv`: one row per recording, with the columns `session, date, rest_s, warning_s, move_s, between_s, electrode_type, electrode_distance_cm, skin_preparation, sensor_model, gain, fs_hz, adc_bits` and `set` (train or test)
- [ ] `QUALITY-REPORT.md`: one row per recording, with the reason for each rejection
- [ ] `DECISIONS.md`: parts 7, 8 and 9
- [ ] `rationale/`: one file per member
- [ ] `ai-tools/`: one screenshot per member
- [ ] The cue video, and one photo of the electrodes for each session, with no faces
- [ ] Two tags, `v0-first` and `v1-report`. At least one commit from each member. The professor added as collaborator

## The basic terms, each with an analogy
| Term | Meaning | Analogy |
|---|---|---|
| Dataset | All your examples together. | The whole deck of flashcards. |
| Label | The answer we take as true for an example. | The answer on the back of the flashcard. |
| Trial | One repetition: cue, action, rest. | One question of a quiz. |
| Session | The recordings of one electrode placement. | One visit to the doctor. |
| Acquisition | How the data comes to exist: measure, sample, store. | Taking a photo. What you did not capture, you cannot add later. |
| Noise | Random errors on every measurement. | The hiss on a radio. You can turn it down, never off. |
| Artifact | A false value that does not come from the thing you want to measure. | A fingerprint on the camera lens. |
| Outlier | A value far from all the others. An error, or a real rare case. | One very tall person in the class photo. |
| Gap | A value that is missing. A blank is not a zero. | A blank on a form. |
| Cleaning | Find these problems and fix or reduce them before the computer learns. | Washing the vegetables before you cook. |
| Feature | A property that describes the example, usually a number. | The clues a detective writes down. |
| Model | The rule the computer learns from the examples. | A recipe where the amounts can change. |
| Test set | Examples the model never saw. Opened once, at the end. | The exam, sealed in an envelope. |
| Leakage | Information the model will not have in real use reaches it during training. | Seeing the exam the night before. |

## References, and where to start your search
1. Merletti R. *Standards for Reporting EMG Data.* ISEK, 1999. Parts 1 and 5 follow it. Its newer checklist: CEDE-Check (https://cede.isek.org/matrix/cede-check/).
2. Riascos Salas J, Molinas M, Lotte F. *Machine learning methods for BCI: challenges, pitfalls and promises.* ESANN 2024. The steps from signal to model, and the fair split. It is about brain signals, and the same steps apply to muscle signals.
3. Wilson G and others. *Good enough practices in scientific computing.* PLOS Computational Biology 2017. How to organise the files.
4. Features and models: the scikit-learn user guide. Models for a microcontroller: emlearn.
