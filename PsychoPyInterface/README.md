# PsychoPy Interface for Gaze Tracking

This package provides an interface between the standalone PsychoPy application and the web-based analytics dashboard for gaze tracking experiments.

## Overview

The PsychoPy Interface allows researchers to:

1. Create and run eye-tracking experiments using PsychoPy
2. Collect gaze data using various eye tracking methods:
   - Native PsychoPy eye tracking via iohub
   - Web-based eye tracking using WebGazer.js
3. Analyze gaze data with built-in tools
4. Visualize gaze patterns, fixations, and saccades
5. Export data to the web-based analytics dashboard

## Directory Structure

- `config.py`: Configuration settings for the interface
- `launcher.py`: GUI launcher for experiments
- `experiments/`: Sample experiments
  - `visual_search.py`: Visual search task with eye tracking
  - `webgazer_demo.py`: Demo of WebGazer.js integration
- `utils/`: Utility modules
  - `eye_tracker.py`: Eye tracking functionality
  - `analysis.py`: Data analysis tools
  - `webgazer_bridge.py`: Bridge to WebGazer.js
- `data/`: Data storage directory
- `resources/`: Resource files

## Requirements

- PsychoPy 2024.2.5 or later
- Python 3.9 or later
- Required Python packages (installed with PsychoPy):
  - numpy
  - pandas
  - matplotlib
  - scipy
  - websockets (for WebGazer integration)

## Usage

### Running the Launcher

The easiest way to use the interface is through the launcher:

```bash
python -m PsychoPyInterface.launcher
```

This will open a GUI where you can select an experiment to run.

### Running Experiments Directly

You can also run experiments directly:

```bash
python -m PsychoPyInterface.experiments.visual_search
python -m PsychoPyInterface.experiments.webgazer_demo
```

### Creating Your Own Experiments

To create your own experiments, use the provided modules as templates:

1. Import the necessary modules:

   ```python
   from PsychoPyInterface.utils import EyeTracker
   from PsychoPyInterface.config import DEFAULT_EXPERIMENT_SETTINGS
   ```

2. Create your experiment class:

   ```python
   class MyExperiment:
       def __init__(self, settings=None):
           # Initialize experiment
           self.settings = DEFAULT_EXPERIMENT_SETTINGS.copy()
           if settings:
               self.settings.update(settings)
           
           # Initialize eye tracker
           self.tracker = EyeTracker(
               win=self.win,
               session_id=self.session_id,
               save_locally=True,
               send_to_server=True
           )
   ```

3. Implement the experiment logic:

   ```python
   def run(self):
       # Set up experiment
       self.setup()
       
       # Calibrate eye tracker
       self.tracker.calibrate()
       
       # Run trials
       for trial in self.trials:
           self.run_trial(trial)
       
       # Clean up
       self.quit()
   ```

## WebGazer Integration

To use WebGazer.js for web-based eye tracking:

1. Import the WebGazer bridge:

   ```python
   from PsychoPyInterface.utils import WebGazerBridge
   ```

2. Initialize the bridge:

   ```python
   bridge = WebGazerBridge(
       session_id="my_session",
       port=8765,
       save_locally=True
   )
   ```

3. Start the bridge and open the client:

   ```python
   bridge.start()
   client_html = bridge.save_client_html()
   webbrowser.open(f'file://{client_html}')
   ```

4. Register a callback for gaze data:

   ```python
   def on_gaze_data(data):
       print(f"Gaze at: {data['x']}, {data['y']}")
   
   bridge.register_gaze_callback(on_gaze_data)
   ```

## Data Analysis

The interface provides tools for analyzing gaze data:

```python
from PsychoPyInterface.utils import analyze_session

# Analyze a session
results = analyze_session("session_id")

# Access analysis results
fixations = results['fixations']
saccades = results['saccades']
heatmap = results['heatmap']
stats = results['stats']

# Plot results
import matplotlib.pyplot as plt
plt.imshow(heatmap, cmap='hot')
plt.show()
```

## License

This package is released under the MIT License.
