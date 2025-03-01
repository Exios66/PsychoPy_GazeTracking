# PsychoPy GazeTracking Interface

A comprehensive interface for eye tracking experiments using PsychoPy, with support for various eye tracking methods including webcam-based tracking, Tobii eye trackers, and simulated data for testing.

## Features

- Web-based interface for controlling eye tracking experiments
- Support for multiple eye tracking methods (webcam, Tobii, simulated)
- Calibration and validation procedures
- Live gaze visualization
- Experiment control and data collection
- Comprehensive logging and error handling

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/PsychoPy_GazeTracking.git
   cd PsychoPy_GazeTracking
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install flask flask-cors psychopy numpy matplotlib opencv-python
   ```

## Running the Application

There are two ways to run the application:

### 1. Minimal Web Interface (No PsychoPy Required)

This mode provides a web interface with simulated data, useful for development and testing:

```
python minimal_app.py
```

The web interface will be available at http://127.0.0.1:5000 (or another port if 5000 is not available).

### 2. Full Application (Requires PsychoPy)

This mode provides the complete functionality with PsychoPy integration:

```
python run_app.py
```

You can also specify additional options:

```
python run_app.py --tracker simulated --port 5001 --no-browser
```

Available options:
- `--tracker`: Specify the tracker type (webcam, tobii, mouse, simulated)
- `--port`: Specify the port for the web interface
- `--host`: Specify the host for the web interface
- `--no-browser`: Do not open the browser automatically
- `--install-deps`: Install missing dependencies

## Troubleshooting

### Import Errors

If you encounter import errors, make sure all dependencies are installed:

```
pip install flask flask-cors psychopy numpy matplotlib opencv-python
```

### PsychoPy Issues

If you encounter issues with PsychoPy, try reinstalling it:

```
pip uninstall psychopy
pip install psychopy
```

### Webcam Access

For webcam-based tracking, make sure your browser has permission to access the webcam.

## Directory Structure

- `PsychoPyInterface/`: Main package directory
  - `Scripts/`: Core scripts for eye tracking functionality
  - `experiments/`: Experiment implementations
  - `utils/`: Utility modules
  - `templates/`: HTML templates for the web interface
  - `static/`: Static files (CSS, JavaScript, images)
- `minimal_app.py`: Minimal web interface launcher
- `run_app.py`: Full application launcher

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- PsychoPy: https://www.psychopy.org/
- Flask: https://flask.palletsprojects.com/
- OpenCV: https://opencv.org/
