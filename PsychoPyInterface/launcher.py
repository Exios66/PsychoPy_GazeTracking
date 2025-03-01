#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PsychoPy Interface Launcher

This script provides a graphical interface for launching
PsychoPy experiments with eye tracking functionality.
"""

import os
import sys
from pathlib import Path

from psychopy import gui, core
from psychopy.hardware import keyboard

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PsychoPyInterface.experiments import VisualSearchExperiment, WebGazerDemo
from PsychoPyInterface.utils import WebGazerBridge
from PsychoPyInterface.config import DATA_DIR


def main():
    """Main function for the launcher."""
    # Create experiment list
    experiments = {
        "Visual Search": VisualSearchExperiment,
        "WebGazer Demo": WebGazerDemo
    }
    
    # Create dialog
    dlg = gui.Dlg(title="PsychoPy Eye Tracking Launcher")
    dlg.addText("Select an experiment to run:")
    dlg.addField("Experiment:", choices=list(experiments.keys()))
    dlg.addField("Participant ID:", "")
    dlg.addField("Session:", "001")
    dlg.addField("Fullscreen:", True)
    
    # Show dialog
    ok_data = dlg.show()
    if not dlg.OK:
        core.quit()
    
    # Get selected experiment
    experiment_name = ok_data[0]
    participant_id = ok_data[1]
    session_id = ok_data[2]
    fullscreen = ok_data[3]
    
    # Create experiment instance
    experiment_class = experiments[experiment_name]
    
    if experiment_name == "Visual Search":
        experiment = experiment_class(settings={
            'fullscreen': fullscreen
        })
    elif experiment_name == "WebGazer Demo":
        experiment = experiment_class()
    else:
        print(f"Unknown experiment: {experiment_name}")
        core.quit()
    
    # Run experiment
    try:
        experiment.run()
    except Exception as e:
        print(f"Error running experiment: {e}")
        core.quit()


if __name__ == "__main__":
    main() 