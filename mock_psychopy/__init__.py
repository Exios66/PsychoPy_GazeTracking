"""
Mock PsychoPy module for development and testing.
This module provides mock implementations of PsychoPy classes and functions
to allow code to be developed and tested without requiring the full PsychoPy package.
"""

# Create mock submodules
class _MockModule:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Create mock classes
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

# Create iohub module
iohub = _MockModule(
    launchHubServer=lambda **kwargs: _MockModule(
        devices=_MockModule(
            eyetracker=None,
            mouse=_MockClass(),
        ),
        quit=lambda: None,
    ),
)

# Create data module
data = _MockModule(
    ExperimentHandler=_MockClass,
    TrialHandler=_MockClass,
    MultiStairHandler=_MockClass,
)

# Create sound module
sound = _MockModule(
    Sound=_MockClass,
)

# Create monitors module
monitors = _MockModule(
    Monitor=_MockClass,
)

# Create logging module
logging = _MockModule(
    console=_MockClass(),
    flush=lambda: None,
    LogFile=_MockClass,
    WARNING=1,
    DATA=2,
    EXP=3,
    INFO=4,
    DEBUG=5,
)

# Create hardware module
hardware = _MockModule(
    keyboard=_MockModule(
        Keyboard=_MockClass,
    ),
)

# Create gui module
gui = _MockModule(
    Dlg=_MockClass,
    DlgFromDict=_MockClass,
) 