#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analysis utilities for eye tracking data.

This module provides functions for analyzing eye tracking data,
including fixation detection, saccade detection, and visualization.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import euclidean
from scipy.ndimage import gaussian_filter
from datetime import datetime

from ..config import DATA_DIR, EYE_TRACKER_SETTINGS


def load_gaze_data(filepath):
    """
    Load gaze data from a JSON file.
    
    Parameters
    ----------
    filepath : str or Path
        Path to the JSON file containing gaze data
        
    Returns
    -------
    dict
        Dictionary containing gaze data and metadata
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def detect_fixations(gaze_data, dispersion_threshold=20, duration_threshold=100):
    """
    Detect fixations in gaze data using the dispersion-threshold identification algorithm.
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
    dispersion_threshold : float
        Maximum dispersion (in pixels) for a fixation
    duration_threshold : float
        Minimum duration (in ms) for a fixation
        
    Returns
    -------
    list
        List of fixations, each containing start time, end time, duration, and position
    """
    # Implementation of the dispersion-threshold identification algorithm
    fixations = []
    current_fixation = None
    
    for i, point in enumerate(gaze_data):
        if current_fixation is None:
            # Start a new fixation
            current_fixation = {
                'start_time': point['timestamp'],
                'points': [point],
                'x': point['x'],
                'y': point['y']
            }
        else:
            # Check if this point belongs to the current fixation
            points = current_fixation['points']
            xs = [p['x'] for p in points]
            ys = [p['y'] for p in points]
            
            # Calculate dispersion
            dispersion = max(max(xs) - min(xs), max(ys) - min(ys))
            
            if dispersion <= dispersion_threshold:
                # Add to current fixation
                current_fixation['points'].append(point)
                
                # Update centroid
                current_fixation['x'] = np.mean(xs + [point['x']])
                current_fixation['y'] = np.mean(ys + [point['y']])
            else:
                # Check if current fixation meets duration threshold
                duration = points[-1]['timestamp'] - points[0]['timestamp']
                if duration >= duration_threshold:
                    # Finalize fixation
                    current_fixation['end_time'] = points[-1]['timestamp']
                    current_fixation['duration'] = duration
                    fixations.append(current_fixation)
                
                # Start a new fixation
                current_fixation = {
                    'start_time': point['timestamp'],
                    'points': [point],
                    'x': point['x'],
                    'y': point['y']
                }
    
    # Check if the last fixation meets the duration threshold
    if current_fixation is not None:
        points = current_fixation['points']
        duration = points[-1]['timestamp'] - points[0]['timestamp']
        if duration >= duration_threshold:
            current_fixation['end_time'] = points[-1]['timestamp']
            current_fixation['duration'] = duration
            fixations.append(current_fixation)
    
    return fixations


def detect_saccades(gaze_data, velocity_threshold=30):
    """
    Detect saccades in gaze data using a velocity-based algorithm.
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
    velocity_threshold : float
        Minimum velocity (in pixels/ms) for a saccade
        
    Returns
    -------
    list
        List of saccades, each containing start time, end time, duration, and amplitude
    """
    # Implementation of a velocity-based saccade detection algorithm
    saccades = []
    in_saccade = False
    saccade_start = None
    
    for i in range(1, len(gaze_data)):
        prev_point = gaze_data[i-1]
        curr_point = gaze_data[i]
        
        # Calculate velocity
        dt = curr_point['timestamp'] - prev_point['timestamp']
        if dt == 0:
            continue
            
        dx = curr_point['x'] - prev_point['x']
        dy = curr_point['y'] - prev_point['y']
        distance = np.sqrt(dx**2 + dy**2)
        velocity = distance / dt
        
        if not in_saccade and velocity >= velocity_threshold:
            # Start of a saccade
            in_saccade = True
            saccade_start = i - 1
        elif in_saccade and velocity < velocity_threshold:
            # End of a saccade
            in_saccade = False
            
            # Calculate saccade properties
            start_point = gaze_data[saccade_start]
            end_point = gaze_data[i]
            
            dx = end_point['x'] - start_point['x']
            dy = end_point['y'] - start_point['y']
            amplitude = np.sqrt(dx**2 + dy**2)
            duration = end_point['timestamp'] - start_point['timestamp']
            
            saccades.append({
                'start_time': start_point['timestamp'],
                'end_time': end_point['timestamp'],
                'duration': duration,
                'amplitude': amplitude,
                'start_x': start_point['x'],
                'start_y': start_point['y'],
                'end_x': end_point['x'],
                'end_y': end_point['y']
            })
    
    return saccades


def create_heatmap(gaze_data, width, height, sigma=30):
    """
    Create a heatmap from gaze data.
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
    width : int
        Width of the heatmap in pixels
    height : int
        Height of the heatmap in pixels
    sigma : float
        Standard deviation of the Gaussian kernel
        
    Returns
    -------
    numpy.ndarray
        2D array representing the heatmap
    """
    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        print("Warning: scipy not installed. Using simple heatmap without Gaussian filter.")
        gaussian_filter = None
    
    # Create an empty heatmap
    heatmap = np.zeros((height, width))
    
    # Add each gaze point to the heatmap
    for point in gaze_data:
        x = int(point['x'] + width/2)
        y = int(point['y'] + height/2)
        
        # Ensure coordinates are within bounds
        if 0 <= x < width and 0 <= y < height:
            heatmap[y, x] += 1
    
    # Apply Gaussian filter if available
    if gaussian_filter is not None:
        heatmap = gaussian_filter(heatmap, sigma=sigma)
    
    # Normalize
    if np.max(heatmap) > 0:
        heatmap = heatmap / np.max(heatmap)
    
    return heatmap


def plot_gaze_data(gaze_data, width, height, output_file=None, show_fixations=True, show_saccades=True):
    """
    Plot gaze data, fixations, and saccades.
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
    width : int
        Width of the plot in pixels
    height : int
        Height of the plot in pixels
    output_file : str, optional
        Path to save the plot
    show_fixations : bool
        Whether to show fixations
    show_saccades : bool
        Whether to show saccades
        
    Returns
    -------
    matplotlib.figure.Figure
        The figure object
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib not installed. Cannot create plot.")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot raw gaze data
    xs = [p['x'] for p in gaze_data]
    ys = [p['y'] for p in gaze_data]
    ax.plot(xs, ys, 'b-', alpha=0.3, linewidth=1)
    
    # Plot fixations
    if show_fixations:
        fixations = detect_fixations(gaze_data)
        for fixation in fixations:
            ax.plot(fixation['x'], fixation['y'], 'ro', markersize=fixation['duration']/50)
    
    # Plot saccades
    if show_saccades:
        saccades = detect_saccades(gaze_data)
        for saccade in saccades:
            ax.arrow(saccade['start_x'], saccade['start_y'], 
                    saccade['end_x'] - saccade['start_x'], 
                    saccade['end_y'] - saccade['start_y'],
                    head_width=10, head_length=10, fc='g', ec='g', alpha=0.5)
    
    # Set limits and labels
    ax.set_xlim(-width/2, width/2)
    ax.set_ylim(-height/2, height/2)
    ax.set_xlabel('X (pixels)')
    ax.set_ylabel('Y (pixels)')
    ax.set_title('Gaze Data Visualization')
    
    # Invert y-axis to match screen coordinates
    ax.invert_yaxis()
    
    # Save if output file is specified
    if output_file:
        plt.savefig(output_file)
    
    return fig


def analyze_session(gaze_data):
    """
    Analyze a session of gaze data.
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
        
    Returns
    -------
    dict
        Dictionary containing analysis results
    """
    # Calculate basic statistics
    timestamps = [p['timestamp'] for p in gaze_data]
    duration = max(timestamps) - min(timestamps)
    
    # Detect fixations and saccades
    fixations = detect_fixations(gaze_data)
    saccades = detect_saccades(gaze_data)
    
    # Calculate fixation statistics
    fixation_durations = [f['duration'] for f in fixations]
    mean_fixation_duration = np.mean(fixation_durations) if fixation_durations else 0
    total_fixation_time = sum(fixation_durations)
    fixation_count = len(fixations)
    
    # Calculate saccade statistics
    saccade_amplitudes = [s['amplitude'] for s in saccades]
    mean_saccade_amplitude = np.mean(saccade_amplitudes) if saccade_amplitudes else 0
    saccade_count = len(saccades)
    
    # Calculate scan path length
    scan_path_length = 0
    for i in range(1, len(gaze_data)):
        prev = gaze_data[i-1]
        curr = gaze_data[i]
        dx = curr['x'] - prev['x']
        dy = curr['y'] - prev['y']
        scan_path_length += np.sqrt(dx**2 + dy**2)
    
    return {
        'duration': duration,
        'sample_count': len(gaze_data),
        'fixation_count': fixation_count,
        'saccade_count': saccade_count,
        'mean_fixation_duration': mean_fixation_duration,
        'total_fixation_time': total_fixation_time,
        'mean_saccade_amplitude': mean_saccade_amplitude,
        'scan_path_length': scan_path_length,
        'fixation_to_saccade_ratio': fixation_count / saccade_count if saccade_count > 0 else 0
    }


def generate_aoi_report(gaze_data, aois):
    """
    Generate a report of gaze data within areas of interest (AOIs).
    
    Parameters
    ----------
    gaze_data : list
        List of gaze data points
    aois : dict
        Dictionary of AOIs, where keys are AOI names and values are
        dictionaries with 'x', 'y', 'width', and 'height' keys
        
    Returns
    -------
    dict
        Dictionary containing AOI analysis results
    """
    # Initialize results
    results = {
        'aoi_data': {},
        'total_gaze_points': len(gaze_data),
        'total_duration': 0
    }
    
    # Initialize AOI data
    for aoi_name in aois:
        results['aoi_data'][aoi_name] = {
            'gaze_points': 0,
            'fixations': 0,
            'total_fixation_duration': 0,
            'mean_fixation_duration': 0,
            'first_fixation_time': None,
            'dwell_time': 0,
            'dwell_time_percent': 0
        }
    
    # Calculate total duration
    timestamps = [p['timestamp'] for p in gaze_data]
    results['total_duration'] = max(timestamps) - min(timestamps)
    
    # Detect fixations
    fixations = detect_fixations(gaze_data)
    
    # Analyze gaze points
    for point in gaze_data:
        for aoi_name, aoi in aois.items():
            # Check if point is within AOI
            if (aoi['x'] - aoi['width']/2 <= point['x'] <= aoi['x'] + aoi['width']/2 and
                aoi['y'] - aoi['height']/2 <= point['y'] <= aoi['y'] + aoi['height']/2):
                results['aoi_data'][aoi_name]['gaze_points'] += 1
    
    # Analyze fixations
    for fixation in fixations:
        for aoi_name, aoi in aois.items():
            # Check if fixation is within AOI
            if (aoi['x'] - aoi['width']/2 <= fixation['x'] <= aoi['x'] + aoi['width']/2 and
                aoi['y'] - aoi['height']/2 <= fixation['y'] <= aoi['y'] + aoi['height']/2):
                # Update fixation count
                results['aoi_data'][aoi_name]['fixations'] += 1
                
                # Update fixation duration
                results['aoi_data'][aoi_name]['total_fixation_duration'] += fixation['duration']
                
                # Update first fixation time
                if (results['aoi_data'][aoi_name]['first_fixation_time'] is None or
                    fixation['start_time'] < results['aoi_data'][aoi_name]['first_fixation_time']):
                    results['aoi_data'][aoi_name]['first_fixation_time'] = fixation['start_time']
    
    # Calculate derived metrics
    for aoi_name in aois:
        aoi_data = results['aoi_data'][aoi_name]
        
        # Calculate mean fixation duration
        if aoi_data['fixations'] > 0:
            aoi_data['mean_fixation_duration'] = aoi_data['total_fixation_duration'] / aoi_data['fixations']
        
        # Calculate dwell time (total time spent looking at AOI)
        aoi_data['dwell_time'] = aoi_data['total_fixation_duration']
        
        # Calculate dwell time percent
        if results['total_duration'] > 0:
            aoi_data['dwell_time_percent'] = (aoi_data['dwell_time'] / results['total_duration']) * 100
    
    return results


def export_data(data, filepath, format='csv'):
    """
    Export data to a file.
    
    Parameters
    ----------
    data : dict or list
        Data to export
    filepath : str or Path
        Path to save the file
    format : str
        Format to save the data in ('csv', 'json', or 'xlsx')
        
    Returns
    -------
    str
        Path to the saved file
    """
    filepath = Path(filepath)
    
    # Create directory if it doesn't exist
    if not filepath.parent.exists():
        os.makedirs(filepath.parent)
    
    # Export based on format
    if format.lower() == 'json':
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    elif format.lower() == 'csv':
        import csv
        
        # Handle different data types
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # List of dictionaries
            with open(filepath, 'w', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        elif isinstance(data, dict):
            # Dictionary
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                for key, value in data.items():
                    writer.writerow([key, value])
        else:
            raise ValueError("Data format not supported for CSV export")
    elif format.lower() == 'xlsx':
        try:
            import pandas as pd
            
            # Convert to DataFrame
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame.from_dict(data, orient='index', columns=['value'])
            else:
                raise ValueError("Data format not supported for Excel export")
            
            # Save to Excel
            df.to_excel(filepath, index=False)
        except ImportError:
            print("Error: pandas not installed. Cannot export to Excel.")
            return None
    else:
        raise ValueError(f"Unsupported export format: {format}")
    
    return str(filepath) 