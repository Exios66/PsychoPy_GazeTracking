# Scripts/adaptive_file_control.py
try:
    from psychopy import visual, event, core
    PSYCHOPY_AVAILABLE = True
except ImportError:
    PSYCHOPY_AVAILABLE = False
    import logging
    logging.warning("PsychoPy not found. Please install it: pip install psychopy")

def run_adaptive_trial_control(win, trial_info, error_threshold=0.5):
    """
    Adaptive trial control example.
    
    Parameters:
      - win: the PsychoPy window.
      - trial_info: dict with trial parameters, must include 'trial_number' and 'error'.
      - error_threshold: error threshold for adjusting trial parameters.
    
    Returns:
      - adapted_fixation_duration: float representing the modified fixation duration.
      - feedback_message: str providing feedback on the adaptation.
    """
    if not PSYCHOPY_AVAILABLE:
        return 1.0, "PsychoPy not available - using default fixation duration"
        
    error = trial_info.get("error", 0)
    if error > error_threshold:
        # Increase fixation duration to allow participant more time to re-center gaze.
        adapted_fixation_duration = 1.5
        feedback_message = (f"Trial {trial_info['trial_number']}: High error ({error:.2f}). "
                            "Increasing fixation duration.")
    else:
        adapted_fixation_duration = 1.0
        feedback_message = (f"Trial {trial_info['trial_number']}: Error acceptable ({error:.2f}).")

    # Optional: Display feedback to the participant
    try:
        feedback = visual.TextStim(win, text=feedback_message)
        feedback.draw()
        win.flip()
        core.wait(1.0)
    except Exception as e:
        logging.warning(f"Could not display feedback: {str(e)}")
    
    return adapted_fixation_duration, feedback_message

if __name__ == '__main__':
    # Standalone test for adaptive trial control
    if PSYCHOPY_AVAILABLE:
        from psychopy import visual, core
        win = visual.Window([1024, 768])
        # Simulate trial information with varying error
        trial_info = {"trial_number": 1, "error": 0.65}
        duration, feedback = run_adaptive_trial_control(win, trial_info, error_threshold=0.5)
        print(f"Adapted Fixation Duration: {duration}")
        print(f"Feedback: {feedback}")
        win.close()
        core.quit()
    else:
        print("PsychoPy not available. Cannot run standalone test.")