#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebGazer Demo Experiment

This experiment demonstrates the integration of PsychoPy with WebGazer.js
for web-based eye tracking.
"""

import os
import json
import time
import webbrowser
from pathlib import Path
from datetime import datetime

from psychopy import visual, core, event, gui
import matplotlib.pyplot as plt

from ..utils import WebGazerBridge, analyze_session
from ..config import DATA_DIR


class WebGazerDemo:
    """Demo experiment using WebGazer.js for eye tracking."""

    def __init__(self, port=8765):
        """
        Initialize the experiment.

        Parameters
        ----------
        port : int, optional
            The port for the WebGazer bridge. Default is 8765.
        """
        # Initialize experiment components
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = DATA_DIR / self.session_id
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize WebGazer bridge
        self.bridge = WebGazerBridge(
            session_id=self.session_id,
            port=port,
            save_locally=True
        )
        
        # Initialize PsychoPy window
        self.win = visual.Window(
            size=(800, 600),
            fullscr=False,
            monitor='testMonitor',
            units='pix',
            color=[0, 0, 0],
            colorSpace='rgb255'
        )
        
        # Create stimuli
        self.instructions = visual.TextStim(
            win=self.win,
            text="WebGazer Demo\n\n"
                 "This experiment demonstrates the integration of PsychoPy with WebGazer.js.\n\n"
                 "A web browser will open with the WebGazer client.\n"
                 "Follow the instructions in the browser to calibrate and connect.\n\n"
                 "Press SPACE to begin.",
            height=24,
            wrapWidth=700,
            color=[255, 255, 255],
            colorSpace='rgb255'
        )
        
        self.waiting_text = visual.TextStim(
            win=self.win,
            text="Waiting for WebGazer client to connect...\n\n"
                 "Please follow the instructions in the browser window.\n\n"
                 "Press ESCAPE to quit.",
            height=24,
            wrapWidth=700,
            color=[255, 255, 255],
            colorSpace='rgb255'
        )
        
        self.connected_text = visual.TextStim(
            win=self.win,
            text="Connected to WebGazer client!\n\n"
                 "Your eye movements are now being tracked.\n"
                 "Look at the targets as they appear.\n\n"
                 "Press SPACE to continue.",
            height=24,
            wrapWidth=700,
            color=[255, 255, 255],
            colorSpace='rgb255'
        )
        
        self.target = visual.GratingStim(
            win=self.win,
            tex=None,
            mask='circle',
            size=40,
            color=[255, 0, 0],
            colorSpace='rgb255'
        )
        
        self.end_text = visual.TextStim(
            win=self.win,
            text="Thank you for participating!\n\n"
                 "The experiment is now complete.\n\n"
                 "Press ESCAPE to exit.",
            height=24,
            wrapWidth=700,
            color=[255, 255, 255],
            colorSpace='rgb255'
        )
        
        # Experiment parameters
        self.n_targets = 9
        self.target_duration = 2.0  # seconds
        self.target_positions = [
            (-300, -200), (0, -200), (300, -200),
            (-300, 0), (0, 0), (300, 0),
            (-300, 200), (0, 200), (300, 200)
        ]
        
        # Data collection
        self.connected = False
        self.gaze_data = []

    def on_gaze_data(self, data):
        """
        Callback for gaze data.

        Parameters
        ----------
        data : dict
            Gaze data point.
        """
        self.gaze_data.append(data)
        self.connected = True

    def run(self):
        """Run the experiment."""
        # Show instructions
        self.instructions.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
        
        # Start WebGazer bridge
        self.bridge.register_gaze_callback(self.on_gaze_data)
        self.bridge.start()
        
        # Save and open client HTML
        client_html = self.bridge.save_client_html()
        webbrowser.open(f'file://{client_html}')
        
        # Wait for connection
        self.waiting_text.draw()
        self.win.flip()
        
        waiting_start = time.time()
        while not self.connected:
            if event.getKeys(['escape']):
                self.quit()
                return
            
            # Check for timeout (2 minutes)
            if time.time() - waiting_start > 120:
                print("Timeout waiting for WebGazer client to connect.")
                self.quit()
                return
            
            self.win.flip()
            time.sleep(0.1)
        
        # Show connected message
        self.connected_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
        
        # Show targets
        for i, pos in enumerate(self.target_positions):
            # Update target position
            self.target.pos = pos
            
            # Draw target
            self.target.draw()
            self.win.flip()
            
            # Wait for target duration
            target_start = time.time()
            while time.time() - target_start < self.target_duration:
                if event.getKeys(['escape']):
                    self.quit()
                    return
                
                time.sleep(0.01)
        
        # Show end screen
        self.end_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['escape'])
        
        # Clean up
        self.quit()

    def analyze_data(self):
        """Analyze the collected gaze data."""
        if not self.gaze_data:
            print("No gaze data to analyze.")
            return
        
        # Convert to the format expected by the analysis functions
        df_data = []
        for point in self.gaze_data:
            df_data.append({
                'timestamp': point['timestamp'],
                'x': point['x'],
                'y': point['y'],
                'session_id': self.session_id,
                'screen_width': point['screen_width'],
                'screen_height': point['screen_height']
            })
        
        # Save to JSON file for analysis
        analysis_file = self.data_dir / "webgazer_analysis_data.json"
        with open(analysis_file, 'w') as f:
            json.dump(df_data, f, indent=2)
        
        # Run analysis
        results = analyze_session(self.session_id, analysis_file)
        
        if results:
            print(f"Analysis complete. Results saved to {self.data_dir}")
            
            # Display heatmap
            plt.figure(figsize=(10, 8))
            plt.imshow(results['heatmap'], cmap='hot', interpolation='bilinear')
            plt.colorbar()
            plt.title('Gaze Heatmap')
            plt.xlabel('X (pixels)')
            plt.ylabel('Y (pixels)')
            
            # Save heatmap
            heatmap_file = self.data_dir / "webgazer_heatmap.png"
            plt.savefig(heatmap_file)
            print(f"Saved heatmap to {heatmap_file}")
            
            # Show statistics
            print("\nGaze Statistics:")
            for key, value in results['stats'].items():
                print(f"{key}: {value}")

    def quit(self):
        """Quit the experiment and clean up."""
        # Stop WebGazer bridge
        self.bridge.stop()
        
        # Close PsychoPy window
        self.win.close()
        
        # Analyze data
        self.analyze_data()
        
        core.quit()


if __name__ == "__main__":
    # Show dialog for experiment settings
    exp_info = {
        'participant': '',
        'port': 8765
    }
    
    dlg = gui.DlgFromDict(
        dictionary=exp_info,
        title='WebGazer Demo',
        fixed=[]
    )
    
    if dlg.OK:
        # Create experiment
        experiment = WebGazerDemo(port=int(exp_info['port']))
        
        # Run experiment
        experiment.run()
    else:
        core.quit() 