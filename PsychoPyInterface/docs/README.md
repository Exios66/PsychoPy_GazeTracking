# PsychoPy Gaze Tracking Experiment

## Overview

This project implements a comprehensive PsychoPy experiment that integrates gaze tracking. The experiment presents visual stimuli while recording gaze data using an eye-tracking device.

## Directory Structure

- **Docs/**: Documentation files (README, participant instructions, debriefing).
- **Data/**: Output data logs from the experiment.
- **Scripts/**: Source code including the main experiment and gaze tracking modules.
- **Stimuli/**: Visual or auditory stimuli files.

## Setup Instructions

1. **Install Dependencies:**
   - Python 3.x
   - PsychoPy (`pip install psychopy`)
2. **Configure the Experiment:**
   - Modify `Scripts/config.json` as needed.
3. **Run the Experiment:**
   - Navigate to the `Scripts` folder and run `python main.py`.

## Troubleshooting

- Ensure that your eye tracker is properly connected and calibrated.
- Check the log file in `Data/` for trial-by-trial output.