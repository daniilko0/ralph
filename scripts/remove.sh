#!/bin/sh

# Stop tmux's session
tmux kill-server

# Delete all ralph's contain
rm -rf projects/ralph
echo "Folder with project deleted."

# Create new virtual environment
mkdir projects/ralph
cd projects/ralph
echo "Setting up virtual environment..."
python3.8 -m venv venv_ralph
echo "Setting up virtual environment finished."
