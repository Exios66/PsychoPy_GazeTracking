"""
Mock psychopy package
"""

# Import submodules
from . import hardware

# Create helper classes
class _MockModule:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class _MockClass:
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, *args, **kwargs):
        return self
    
    def __getattr__(self, name):
        return _MockClass()

# Create core module
core = _MockModule(
    getTime=lambda: 0.0,
    wait=lambda x: None,
    Clock=_MockClass,
    CountdownTimer=_MockClass,
    StaticPeriod=_MockClass,
    quit=lambda: None,
)

# Create visual module
visual = _MockModule(
    Window=_MockClass,
    TextStim=_MockClass,
    ImageStim=_MockClass,
    GratingStim=_MockClass,
    ShapeStim=_MockClass,
    Rect=_MockClass,
    Circle=_MockClass,
    Line=_MockClass,
)

# Create event module
event = _MockModule(
    getKeys=lambda keyList=None: [],
    waitKeys=lambda keyList=None: [],
    Mouse=_MockClass,
    clearEvents=lambda: None,
)

# Create data module
data = _MockModule(
    ExperimentHandler=_MockClass,
    TrialHandler=_MockClass,
    MultiStairHandler=_MockClass,
)

# Create gui module
gui = _MockModule(
    Dlg=_MockClass,
    DlgFromDict=_MockClass,
)
