#!/bin/bash

# Define environment name
VENV_NAME="venv"

echo "Setting up virtual environment..."

# 1. Create Virtual Environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment '$VENV_NAME'..."
    python3 -m venv $VENV_NAME
else
    echo "Virtual environment '$VENV_NAME' already exists."
fi

# 2. Activate the environment
echo "Activating virtual environment..."
source $VENV_NAME/bin/activate

# 3. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found!"
fi

echo ""
echo "--------------------------------------------------------"
echo "Setup Complete!"
echo ""
echo "To activate the environment in your shell, run:"
echo "    source $VENV_NAME/bin/activate"
echo ""
echo "IMPORTANT REMINDER:"
echo "The 'agents' library required for the agent script is NOT in requirements.txt"
echo "to avoid conflicts with the wrong PyPI package."
echo "Please install it manually using the command provided by your"
echo "Agent Builder source (e.g., pip install git+... or pip install openai-agents)."
echo "--------------------------------------------------------"
