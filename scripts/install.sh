#!/bin/sh

# Copy downloaded bundle to project's directory
yes | cp -rf {$PWD}/* /home/ubuntu/projects/ralph

# Create new virtual environment
mkdir /home/ubuntu/projects/ralph
cd /home/ubuntu/projects/ralph
echo "Setting up virtual environment..."
/home/ubuntu/.python/bin//python3.8 -m venv venv_ralph
echo "Setting up virtual environment finished."

# Activate this virtual environment
echo "Activating virtual environment..."
. /home/ubuntu/projects/ralph/venv_ralph/bin/activate
echo "Virtual environment activated."