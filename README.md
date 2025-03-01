# PsychoPy Gaze Tracking

## Overview
This repository contains a gaze tracking application built with PsychoPy and a web-based analytics dashboard built with React.

## Repository Structure
- `GazeAnalytics/`: Web application for visualizing and analyzing gaze data
  - `client/`: React frontend
  - `server/`: Backend server
  - `shared/`: Shared code between client and server
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

### PsychoPy Experiments
PsychoPy experiments can be run using the PsychoPy Builder or by executing Python scripts directly.

## Troubleshooting

### Common Issues
- If you encounter issues with PsychoPy dependencies, try installing the standalone PsychoPy application from [psychopy.org](https://www.psychopy.org/download.html).
- For macOS users, some dependencies may require additional system libraries. Consider using Homebrew to install them:
  ```bash
  brew install hdf5 libusb portaudio
  ```

## License
MIT
