# PsychoPy Gaze Tracking

## Overview
This repository contains a gaze tracking application built with PsychoPy and a web-based analytics dashboard built with React.

## Repository Structure
- `GazeAnalytics/`: Web application for visualizing and analyzing gaze data
  - `client/`: React frontend
  - `server/`: Backend server
  - `shared/`: Shared code between client and server
- `PsychoPyInterface/`: Interface for the standalone PsychoPy application
  - `experiments/`: Sample eye-tracking experiments
  - `utils/`: Utility modules for eye tracking and analysis
  - `data/`: Data storage directory
  - `resources/`: Resource files
- `requirements.txt`: Python dependencies
- `package.json`: Node.js dependencies

## Setup Instructions

### Prerequisites
- Python 3.9+ 
- Node.js 20.0+
- npm 9.0+

### Python Environment Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the core Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Optional: Install additional dependencies based on your needs:
   - For GUI development: `pip install wxPython`
   - For improved timing: `pip install psychtoolbox`
   - For video playback: `pip install ffpyplayer`
   - For audio processing: `pip install soundfile`
   - For database access: `pip install psycopg2-binary`
   - For eye tracking: `pip install tobii-research pylink`

### Node.js Setup
1. Install Node.js dependencies:
   ```bash
   cd GazeAnalytics
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Running the Application

### Web Dashboard
```bash
cd GazeAnalytics
npm run dev
```

### PsychoPy Interface
The PsychoPy Interface provides tools for creating and running eye-tracking experiments using the standalone PsychoPy application.

#### Using the Launcher
The easiest way to use the interface is through the launcher:

```bash
python -m PsychoPyInterface.launcher
```

This will open a GUI where you can select an experiment to run.

#### Running Experiments Directly
You can also run experiments directly:

```bash
python -m PsychoPyInterface.experiments.visual_search
python -m PsychoPyInterface.experiments.webgazer_demo
```

#### Available Experiments
1. **Visual Search**: A visual search task where participants search for a target among distractors while their eye movements are tracked.
2. **WebGazer Demo**: A demonstration of WebGazer.js integration for web-based eye tracking.

#### Creating Your Own Experiments
See the [PsychoPyInterface README](PsychoPyInterface/README.md) for detailed instructions on creating your own experiments.

## Features

### Eye Tracking Methods
- **Native PsychoPy Eye Tracking**: Using PsychoPy's iohub interface
- **WebGazer.js Integration**: Web-based eye tracking using a webcam
- **External Eye Trackers**: Support for external eye trackers via PsychoPy

### Data Analysis
- **Fixation Detection**: Identify fixations in gaze data
- **Saccade Detection**: Identify saccades in gaze data
- **Heatmap Generation**: Create heatmaps of gaze patterns
- **Statistical Analysis**: Calculate metrics like fixation duration, saccade amplitude, etc.

### Visualization
- **Real-time Visualization**: View gaze data in real-time
- **Post-hoc Analysis**: Analyze gaze data after the experiment
- **Interactive Dashboards**: Explore gaze data through interactive visualizations

## Troubleshooting

### Common Issues
- If you encounter issues with PsychoPy dependencies, try installing the standalone PsychoPy application from [psychopy.org](https://www.psychopy.org/download.html).
- For macOS users, some dependencies may require additional system libraries. Consider using Homebrew to install them:
  ```bash
  brew install hdf5 libusb portaudio
  ```
- For WebGazer.js integration, ensure your browser has permission to access the webcam.

## License
MIT
