"""
Mock psychopy.hardware.keyboard module
"""

class Keyboard:
    """Mock Keyboard class"""
    
    def __init__(self, *args, **kwargs):
        pass
        
    def getKeys(self, keyList=None, waitRelease=True, clear=True):
        """Get pressed keys"""
        return []
        
    def clearEvents(self):
        """Clear events"""
        pass

# Create module-level functions
def getKeys(keyList=None, waitRelease=True, clear=True):
    """Get pressed keys"""
    return [] 