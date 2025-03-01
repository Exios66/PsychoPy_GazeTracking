@echo off
REM Script to install the package in development mode

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install package in development mode
echo Installing package in development mode...
pip install -e .[dev,web]

REM Run tests
echo Running tests...
python tests\run_tests.py

echo Installation complete!
echo To activate the virtual environment, run: venv\Scripts\activate
echo To run the launcher, run: psychopy-gaze-launcher

pause 