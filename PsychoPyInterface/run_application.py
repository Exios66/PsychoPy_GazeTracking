#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PsychoPy GazeTracking Application Launcher

This script serves as the main entry point for the PsychoPy GazeTracking application.
It initializes all components, starts a web server for remote control and visualization,
and provides a unified interface for running experiments, calibration, and validation.

Features:
- Web interface for experiment control and visualization
- Unified initialization of all components
- Automatic detection of available hardware
- Comprehensive logging and error handling
- Support for different eye tracking methods
"""

import os
import sys
import json
import logging
import argparse
import webbrowser
import threading
import traceback
from datetime import datetime
from pathlib import Path
import socket
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('application')

# Add the parent directory to the path so we can import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Try to import required dependencies
try:
    import flask
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    logger.error("Flask not found. Web interface will not be available.")
    logger.error("Please install Flask: pip install flask flask-cors")
    FLASK_AVAILABLE = False

try:
    from psychopy import visual, core, event
    PSYCHOPY_AVAILABLE = True
except ImportError:
    logger.error("PsychoPy not found. Please install it: pip install psychopy")
    PSYCHOPY_AVAILABLE = False

# Import local modules with error handling - define placeholders for missing modules
GazeTracker = None
run_calibration = None
run_validation = None
setup_logger = None
create_log_file = None
log_message = None
close_log_file = None
check_calibration_and_adapt = None
VisualSearchExperiment = None
LOCAL_MODULES_AVAILABLE = False

# Try to import local modules
try:
    # Import modules individually to handle missing modules gracefully
    try:
        from PsychoPyInterface.Scripts.gaze_tracking import GazeTracker
    except ImportError:
        logger.error("Could not import GazeTracker")
        
    try:
        from PsychoPyInterface.Scripts.calibration import run_calibration
    except ImportError:
        logger.error("Could not import run_calibration")
        
    try:
        from PsychoPyInterface.Scripts.validation import run_validation
    except ImportError:
        logger.error("Could not import run_validation")
        
    try:
        from PsychoPyInterface.Scripts.logging_utils import setup_logger, create_log_file, log_message, close_log_file
    except ImportError:
        logger.error("Could not import logging utilities")
        
    try:
        from PsychoPyInterface.Scripts.adaptive_control import check_calibration_and_adapt
    except ImportError:
        logger.error("Could not import check_calibration_and_adapt")
        
    try:
        from PsychoPyInterface.experiments.visual_search import VisualSearchExperiment
    except ImportError:
        logger.error("Could not import VisualSearchExperiment")
    
    # Check if essential modules were imported
    if GazeTracker and run_calibration and run_validation:
        LOCAL_MODULES_AVAILABLE = True
    else:
        logger.warning("Some essential modules could not be imported")
        
except Exception as e:
    logger.error(f"Error importing local modules: {str(e)}")
    logger.error(traceback.format_exc())

# Try to import optional dependencies
try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import io
    import base64
    VISUALIZATION_AVAILABLE = True
except ImportError:
    logger.error("Visualization libraries not found. Visualization features will be limited.")
    logger.error("Please install: pip install numpy matplotlib")
    VISUALIZATION_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not found. Webcam-based tracking will not be available.")
    logger.warning("Please install: pip install opencv-python")
    OPENCV_AVAILABLE = False

# Application configuration
DEFAULT_CONFIG = {
    "web_interface": {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": False,
        "open_browser": True
    },
    "experiment": {
        "fullscreen": False,
        "screen_width": 1024,
        "screen_height": 768,
        "background_color": [128, 128, 128],
        "text_color": [255, 255, 255]
    },
    "eye_tracking": {
        "tracker_type": "webcam",  # Options: webcam, tobii, mouse, simulated
        "webcam_id": 0,
        "calibration_points": 9,
        "validation_threshold": 1.0
    },
    "data": {
        "save_directory": "data",
        "auto_save_interval": 60  # seconds
    }
}

class PsychoPyGazeTrackingApp:
    """Main application class for PsychoPy GazeTracking."""
    
    def __init__(self, config=None):
        """
        Initialize the application.
        
        Parameters:
        -----------
        config : dict, optional
            Configuration dictionary. If None, default config will be used.
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self._update_config(config)
            
        # Set up logging
        self.log_dir = Path(self.config["data"]["save_directory"]) / "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = setup_logger("app", log_file=log_file)
        self.logger.info("Application initializing")
        
        # Initialize state variables
        self.window = None
        self.tracker = None
        self.experiment = None
        self.calibration_results = None
        self.validation_results = None
        self.is_running = False
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize Flask app if available
        self.flask_app = None
        if FLASK_AVAILABLE:
            self._setup_flask_app()
    
    def _update_config(self, config):
        """
        Update configuration with user-provided values.
        
        Parameters:
        -----------
        config : dict
            Configuration dictionary to merge with defaults
        """
        for section, values in config.items():
            if section in self.config:
                if isinstance(self.config[section], dict) and isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values
    
    def _setup_flask_app(self):
        """Set up Flask web application."""
        self.flask_app = Flask(__name__, 
                              static_folder=str(current_dir / "static"),
                              template_folder=str(current_dir / "templates"))
        CORS(self.flask_app)
        
        # Register routes
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self.flask_app.route('/api/status')
        def status():
            return jsonify({
                'psychopy_available': PSYCHOPY_AVAILABLE,
                'opencv_available': OPENCV_AVAILABLE,
                'visualization_available': VISUALIZATION_AVAILABLE,
                'local_modules_available': LOCAL_MODULES_AVAILABLE,
                'tracker_initialized': self.tracker is not None,
                'experiment_running': self.is_running,
                'session_id': self.session_id,
                'calibration_results': self.calibration_results,
                'validation_results': self.validation_results
            })
        
        @self.flask_app.route('/api/config', methods=['GET', 'POST'])
        def config():
            if request.method == 'POST':
                try:
                    new_config = request.json
                    self._update_config(new_config)
                    return jsonify({'status': 'success', 'config': self.config})
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 400
            else:
                return jsonify(self.config)
        
        @self.flask_app.route('/api/initialize', methods=['POST'])
        def initialize():
            try:
                result = self.initialize_components()
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                self.logger.error(f"Error initializing components: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/calibrate', methods=['POST'])
        def calibrate():
            try:
                result = self.run_calibration()
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                self.logger.error(f"Error during calibration: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/validate', methods=['POST'])
        def validate():
            try:
                result = self.run_validation()
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                self.logger.error(f"Error during validation: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/experiment/start', methods=['POST'])
        def start_experiment():
            try:
                experiment_type = request.json.get('type', 'visual_search')
                params = request.json.get('params', {})
                result = self.start_experiment(experiment_type, params)
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                self.logger.error(f"Error starting experiment: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/experiment/stop', methods=['POST'])
        def stop_experiment():
            try:
                result = self.stop_experiment()
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                self.logger.error(f"Error stopping experiment: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/gaze_data', methods=['GET'])
        def get_gaze_data():
            try:
                if self.tracker:
                    gaze_data = self.tracker.get_gaze_data()
                    return jsonify({'status': 'success', 'data': gaze_data})
                else:
                    return jsonify({'status': 'error', 'message': 'Tracker not initialized'}), 400
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/visualization/calibration', methods=['GET'])
        def get_calibration_visualization():
            if not VISUALIZATION_AVAILABLE or not self.calibration_results:
                return jsonify({'status': 'error', 'message': 'Visualization not available or no calibration data'}), 400
                
            try:
                # Generate visualization
                fig = plt.figure(figsize=(10, 8))
                
                # Plot target vs. gaze points
                ax = fig.add_subplot(111)
                
                if 'target_points' in self.calibration_results and 'gaze_points' in self.calibration_results:
                    target_points = self.calibration_results['target_points']
                    gaze_points = self.calibration_results['gaze_points']
                    
                    # Extract x and y coordinates
                    target_x = [p[0] for p in target_points]
                    target_y = [p[1] for p in target_points]
                    gaze_x = [p[0] for p in gaze_points]
                    gaze_y = [p[1] for p in gaze_points]
                    
                    # Plot points
                    ax.scatter(target_x, target_y, color='blue', label='Target', s=100)
                    ax.scatter(gaze_x, gaze_y, color='red', alpha=0.7, label='Gaze', s=50)
                    
                    # Draw lines connecting corresponding points
                    for i in range(len(target_x)):
                        ax.plot([target_x[i], gaze_x[i]], [target_y[i], gaze_y[i]], 'k-', alpha=0.3)
                
                ax.set_title('Calibration Results')
                ax.set_xlabel('X Coordinate')
                ax.set_ylabel('Y Coordinate')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Convert plot to image
                canvas = FigureCanvas(fig)
                img_io = io.BytesIO()
                canvas.print_png(img_io)
                img_io.seek(0)
                img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
                plt.close(fig)
                
                return jsonify({
                    'status': 'success', 
                    'image': f'data:image/png;base64,{img_data}',
                    'metrics': {
                        'average_error': self.calibration_results.get('average', 'N/A'),
                        'max_error': self.calibration_results.get('max', 'N/A'),
                        'quality': self.calibration_results.get('quality', 'N/A')
                    }
                })
            except Exception as e:
                self.logger.error(f"Error generating visualization: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/webcam_list', methods=['GET'])
        def get_webcam_list():
            if not OPENCV_AVAILABLE:
                return jsonify({'status': 'error', 'message': 'OpenCV not available'}), 400
                
            try:
                webcams = self._detect_webcams()
                return jsonify({'status': 'success', 'webcams': webcams})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def _detect_webcams(self, max_cameras=10):
        """
        Detect available webcams.
        
        Parameters:
        -----------
        max_cameras : int
            Maximum number of cameras to check
            
        Returns:
        --------
        list
            List of dictionaries with webcam information
        """
        if not OPENCV_AVAILABLE:
            return []
            
        webcams = []
        
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        webcams.append({
                            'id': i,
                            'name': f'Camera {i}',
                            'resolution': f'{int(width)}x{int(height)}',
                            'fps': int(fps) if fps > 0 else 'Unknown'
                        })
                cap.release()
            except Exception as e:
                self.logger.debug(f"Error checking camera {i}: {e}")
        
        return webcams
    
    def initialize_components(self):
        """
        Initialize PsychoPy window and eye tracker.
        
        Returns:
        --------
        dict
            Initialization results
        """
        if not PSYCHOPY_AVAILABLE:
            raise ImportError("PsychoPy is required but not available")
            
        try:
            # Close existing window if open
            if self.window is not None:
                self.window.close()
            
            # Create PsychoPy window
            self.window = visual.Window(
                size=(
                    self.config["experiment"]["screen_width"],
                    self.config["experiment"]["screen_height"]
                ),
                fullscr=self.config["experiment"]["fullscreen"],
                monitor="testMonitor",
                units="norm",
                color=[c/255 for c in self.config["experiment"]["background_color"]],
                colorSpace='rgb',
                winType='pyglet'
            )
            
            # Initialize eye tracker
            tracker_type = self.config["eye_tracking"]["tracker_type"]
            webcam_id = self.config["eye_tracking"]["webcam_id"]
            
            self.tracker = GazeTracker(
                calibration_threshold=self.config["eye_tracking"]["validation_threshold"],
                tracker_type=tracker_type,
                webcam_id=webcam_id
            )
            
            self.logger.info(f"Components initialized: Window and {tracker_type} tracker")
            
            return {
                'window': {
                    'width': self.config["experiment"]["screen_width"],
                    'height': self.config["experiment"]["screen_height"],
                    'fullscreen': self.config["experiment"]["fullscreen"]
                },
                'tracker': {
                    'type': tracker_type,
                    'webcam_id': webcam_id if tracker_type == 'webcam' else None,
                    'initialized': self.tracker.initialized
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def run_calibration(self):
        """
        Run eye tracker calibration.
        
        Returns:
        --------
        dict
            Calibration results
        """
        if not self.tracker:
            raise RuntimeError("Tracker not initialized. Call initialize_components first.")
            
        try:
            # Run calibration
            self.logger.info("Starting calibration")
            
            # Use the tracker's calibration method
            calibration_points = self.config["eye_tracking"]["calibration_points"]
            
            # Generate calibration points if a number was provided
            if isinstance(calibration_points, int):
                if calibration_points == 9:
                    # 3x3 grid
                    points = []
                    for y in [-0.8, 0, 0.8]:
                        for x in [-0.8, 0, 0.8]:
                            points.append((x, y))
                elif calibration_points == 5:
                    # 5-point calibration
                    points = [
                        (0, 0),      # Center
                        (-0.8, 0.8), # Top-left
                        (0.8, 0.8),  # Top-right
                        (-0.8, -0.8),# Bottom-left
                        (0.8, -0.8)  # Bottom-right
                    ]
                else:
                    # Default to corners and center
                    points = [
                        (0, 0),      # Center
                        (-0.8, 0.8), # Top-left
                        (0.8, 0.8),  # Top-right
                        (-0.8, -0.8),# Bottom-left
                        (0.8, -0.8)  # Bottom-right
                    ]
            else:
                # Use provided points
                points = calibration_points
                
            self.calibration_results = self.tracker.calibrate(points, self.window)
            
            self.logger.info(f"Calibration completed: {self.calibration_results}")
            return self.calibration_results
            
        except Exception as e:
            self.logger.error(f"Error during calibration: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def run_validation(self):
        """
        Run eye tracker validation.
        
        Returns:
        --------
        dict
            Validation results
        """
        if not self.tracker:
            raise RuntimeError("Tracker not initialized. Call initialize_components first.")
            
        try:
            # Run validation
            self.logger.info("Starting validation")
            
            # Create validation config
            validation_config = {
                "window_width": self.config["experiment"]["screen_width"],
                "window_height": self.config["experiment"]["screen_height"],
                "full_screen": self.config["experiment"]["fullscreen"],
                "validation_threshold": self.config["eye_tracking"]["validation_threshold"]
            }
            
            # Run validation
            self.validation_results = run_validation(validation_config, self.tracker)
            
            self.logger.info(f"Validation completed: {self.validation_results}")
            return self.validation_results
            
        except Exception as e:
            self.logger.error(f"Error during validation: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def start_experiment(self, experiment_type='visual_search', params=None):
        """
        Start an experiment.
        
        Parameters:
        -----------
        experiment_type : str
            Type of experiment to run
        params : dict, optional
            Additional parameters for the experiment
            
        Returns:
        --------
        dict
            Result of starting the experiment
        """
        if self.is_running:
            raise RuntimeError("An experiment is already running")
            
        if not params:
            params = {}
            
        try:
            self.logger.info(f"Starting {experiment_type} experiment")
            
            if experiment_type == 'visual_search':
                # Create experiment settings
                settings = {
                    "fullscreen": self.config["experiment"]["fullscreen"],
                    "screen_width": self.config["experiment"]["screen_width"],
                    "screen_height": self.config["experiment"]["screen_height"],
                    "background_color": self.config["experiment"]["background_color"],
                    "text_color": self.config["experiment"]["text_color"]
                }
                
                # Add any additional parameters
                settings.update(params)
                
                # Create experiment instance
                self.experiment = VisualSearchExperiment(settings=settings)
                
                # Start experiment in a separate thread
                self.is_running = True
                threading.Thread(target=self._run_experiment_thread).start()
                
                return {
                    'experiment_type': experiment_type,
                    'settings': settings,
                    'status': 'started'
                }
            else:
                raise ValueError(f"Unknown experiment type: {experiment_type}")
                
        except Exception as e:
            self.logger.error(f"Error starting experiment: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _run_experiment_thread(self):
        """Run experiment in a separate thread."""
        try:
            # Run the experiment
            result = self.experiment.run()
            
            # Update state
            self.is_running = False
            
            self.logger.info(f"Experiment completed with result: {result}")
            
        except Exception as e:
            self.logger.error(f"Error during experiment: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.is_running = False
    
    def stop_experiment(self):
        """
        Stop the running experiment.
        
        Returns:
        --------
        dict
            Result of stopping the experiment
        """
        if not self.is_running:
            return {'status': 'not_running'}
            
        try:
            self.logger.info("Stopping experiment")
            
            # Set abort flag if experiment supports it
            if hasattr(self.experiment, 'aborted'):
                self.experiment.aborted = True
                
            # Wait for experiment to stop
            timeout = 5.0  # seconds
            start_time = time.time()
            
            while self.is_running and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            if self.is_running:
                self.logger.warning("Experiment did not stop gracefully, forcing quit")
                self.is_running = False
                
                # Force cleanup
                if hasattr(self.experiment, 'quit'):
                    self.experiment.quit()
            
            return {'status': 'stopped'}
            
        except Exception as e:
            self.logger.error(f"Error stopping experiment: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.is_running = False  # Ensure flag is reset
            raise
    
    def run_web_interface(self):
        """Start the web interface."""
        if not FLASK_AVAILABLE or not self.flask_app:
            self.logger.error("Flask not available. Cannot start web interface.")
            return False
            
        try:
            host = self.config["web_interface"]["host"]
            port = self.config["web_interface"]["port"]
            debug = self.config["web_interface"]["debug"]
            open_browser = self.config["web_interface"]["open_browser"]
            
            # Check if port is available
            if not self._is_port_available(host, port):
                # Try to find an available port
                for p in range(port + 1, port + 100):
                    if self._is_port_available(host, p):
                        self.logger.warning(f"Port {port} is not available. Using port {p} instead.")
                        port = p
                        break
                else:
                    self.logger.error(f"Could not find an available port. Web interface will not start.")
                    return False
            
            # Open browser in a separate thread if requested
            if open_browser:
                threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
            
            # Start Flask app
            self.logger.info(f"Starting web interface at http://{host}:{port}")
            self.flask_app.run(host=host, port=port, debug=debug, use_reloader=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting web interface: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _is_port_available(self, host, port):
        """Check if a port is available."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.close()
            return True
        except:
            return False
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.info("Cleaning up resources")
            
            # Stop experiment if running
            if self.is_running:
                self.stop_experiment()
            
            # Close window
            if self.window:
                self.window.close()
                self.window = None
            
            # Close tracker
            if self.tracker:
                self.tracker.close()
                self.tracker = None
                
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.logger.error(traceback.format_exc())

def load_config_file(config_path):
    """
    Load configuration from a JSON file.
    
    Parameters:
    -----------
    config_path : str
        Path to the configuration file
        
    Returns:
    --------
    dict
        Configuration dictionary or None if loading fails
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration file: {str(e)}")
        return None

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='PsychoPy GazeTracking Application')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--host', type=str, help='Host for web interface')
    parser.add_argument('--port', type=int, help='Port for web interface')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--fullscreen', action='store_true', help='Run in fullscreen mode')
    parser.add_argument('--tracker', type=str, help='Tracker type (webcam, tobii, mouse, simulated)')
    parser.add_argument('--webcam-id', type=int, help='Webcam ID for webcam tracker')
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        config = load_config_file(args.config)
    
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # Override config with command line arguments
    if args.host:
        config["web_interface"]["host"] = args.host
    if args.port:
        config["web_interface"]["port"] = args.port
    if args.no_browser:
        config["web_interface"]["open_browser"] = False
    if args.fullscreen:
        config["experiment"]["fullscreen"] = True
    if args.tracker:
        config["eye_tracking"]["tracker_type"] = args.tracker
    if args.webcam_id is not None:
        config["eye_tracking"]["webcam_id"] = args.webcam_id
    
    # Create and run application
    app = PsychoPyGazeTrackingApp(config)
    
    try:
        # Run web interface
        app.run_web_interface()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        app.cleanup()

if __name__ == "__main__":
    main() 