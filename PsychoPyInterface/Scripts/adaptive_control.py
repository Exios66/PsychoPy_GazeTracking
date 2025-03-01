# Scripts/adaptive_control.py
import os
import logging
try:
    from psychopy import visual, event, core
    PSYCHOPY_AVAILABLE = True
except ImportError:
    PSYCHOPY_AVAILABLE = False
    logging.warning("PsychoPy not found. Please install it: pip install psychopy")

from calibration_analysis import analyze_calibration

def check_calibration_and_adapt(win, calibration_log_path, threshold):
    """
    Analyzes the calibration data and provides feedback.
    If the average error is above the specified threshold,
    returns True (i.e., re-calibration is recommended); otherwise False.
    
    Parameters:
    -----------
    win : psychopy.visual.Window
        PsychoPy window to draw on
    calibration_log_path : str or Path
        Path to the calibration log file
    threshold : float
        Error threshold for determining if recalibration is needed
        
    Returns:
    --------
    bool
        True if recalibration is recommended, False otherwise
    """
    if not PSYCHOPY_AVAILABLE:
        logging.warning("PsychoPy not available. Cannot check calibration.")
        return True  # Recommend recalibration if PsychoPy is not available
        
    # Check if the calibration log file exists
    if not os.path.exists(calibration_log_path):
        message = "Calibration data not found.\nPlease run calibration again."
        recalibrate = True
    else:
        # Analyze the calibration data
        try:
            analysis = analyze_calibration(calibration_log_path)
            if analysis is None:
                message = "Calibration data could not be analyzed.\nPlease run calibration again."
                recalibrate = True
            else:
                avg_error = analysis["average"]
                message = f"Calibration average error: {avg_error:.3f}.\n"
                if avg_error > threshold:
                    message += "Error is above threshold.\nPlease recalibrate."
                    recalibrate = True
                else:
                    message += "Calibration is within acceptable limits.\nPress any key to continue."
                    recalibrate = False
        except Exception as e:
            logging.error(f"Error analyzing calibration data: {str(e)}")
            message = f"Error analyzing calibration data: {str(e)}.\nPlease run calibration again."
            recalibrate = True

    # Display feedback to the user
    try:
        feedback = visual.TextStim(win, text=message)
        feedback.draw()
        win.flip()
        event.waitKeys()
    except Exception as e:
        logging.error(f"Error displaying calibration feedback: {str(e)}")
        
    return recalibrate

if __name__ == '__main__':
    # Standalone test for adaptive control (update log file path and threshold as needed)
    if PSYCHOPY_AVAILABLE:
        from psychopy import visual
        win = visual.Window([1024, 768])
        log_path = os.path.join("Data", "calibration_log.txt")
        threshold = 0.2
        need_recalibration = check_calibration_and_adapt(win, log_path, threshold)
        if need_recalibration:
            print("Recalibration is recommended.")
        else:
            print("Calibration is acceptable.")
        win.close()
        core.quit()
    else:
        print("PsychoPy not available. Cannot run standalone test.")