#!/bin/bash

# AI Job Application Assistant Runner Script

# Make sure the script is executable
# chmod +x run.sh

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Please install venv package and try again."
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/requirements_installed" ]; then
    echo "🔧 Installing requirements..."
    pip install -r requirements.txt --no-deps
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements. Please check requirements.txt and try again."
        exit 1
    fi
    
    # Create a flag file to indicate requirements are installed
    touch venv/requirements_installed
fi

# Create data folder if it doesn't exist
mkdir -p data_folder

# Run the application with any provided arguments
echo "🚀 Running AI Job Application Assistant..."
python3 main.py "$@"

# Deactivate virtual environment
deactivate

echo "✅ Done!"

