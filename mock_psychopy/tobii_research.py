"""
Mock Tobii Research module for development and testing.
"""

from ._mock_base import _MockModule, _MockClass

# Constants
EYETRACKER_GAZE_DATA = "gaze_data"
CALIBRATION_STATUS_SUCCESS = 1
UNMASKED_RENDERER_WEBGL = 0x9246

def find_all_eyetrackers():
    """Mock function to find Tobii eye trackers."""
    return [
        _MockModule(
            model="Tobii Pro Spectrum",
            serial_number="TS123456",
            subscribe_to=lambda *args, **kwargs: None,
            unsubscribe_from=lambda *args, **kwargs: None,
        )
    ]

class ScreenBasedCalibration:
    """Mock class for Tobii screen-based calibration."""
    
    def __init__(self, tracker):
        self.tracker = tracker
        
    def enter_calibration_mode(self):
        """Enter calibration mode."""
        pass
        
    def collect_data(self, x, y):
        """Collect calibration data for a point."""
        pass
        
    def compute_and_apply(self):
        """Compute and apply calibration."""
        return _MockModule(status=CALIBRATION_STATUS_SUCCESS)
        
    def leave_calibration_mode(self):
        """Leave calibration mode."""
        pass 