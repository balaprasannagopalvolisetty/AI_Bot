@echo off
echo AI Job Application Assistant Runner Script

REM Check if Python 3 is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo X Python is not installed. Please install Python 3 and try again.
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    
    if %ERRORLEVEL% NEQ 0 (
        echo X Failed to create virtual environment. Please install venv package and try again.
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if requirements are installed
if not exist venv\requirements_installed (
    echo Installing requirements...
    pip install -r requirements.txt --no-deps
    
    if %ERRORLEVEL% NEQ 0 (
        echo X Failed to install requirements. Please check requirements.txt and try again.
        exit /b 1
    )
    
    REM Create a flag file to indicate requirements are installed
    echo. > venv\requirements_installed
)

REM Create data folder if it doesn't exist
if not exist data_folder mkdir data_folder

REM Run the application with any provided arguments
echo Running AI Job Application Assistant...
python main.py %*

REM Deactivate virtual environment
deactivate

echo Done!

