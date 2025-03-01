# Scripts/adaptive_control.py
import os
from psychopy import visual, event, core
from calibration_analysis import analyze_calibration

def check_calibration_and_adapt(win, calibration_log_path, threshold):
    """
    Analyzes the calibration data and provides feedback.
    If the average error is above the specified threshold,
    returns True (i.e., re-calibration is recommended); otherwise False.
    """
    analysis = analyze_calibration(calibration_log_path)
    if analysis is None:
        message = "Calibration data not found.\nPlease run calibration again."
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

    feedback = visual.TextStim(win, text=message)
    feedback.draw()
    win.flip()
    event.waitKeys()
    return recalibrate

if __name__ == '__main__':
    # Standalone test for adaptive control (update log file path and threshold as needed)
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