#!/bin/sh

# Stop tmux's session
tmux kill-server

# Delete all ralph's contain
rm -rf /home/ubuntu/projects/ralph
echo "Folder with project deleted."

# Create new virtual environment
mkdir /home/ubuntu/projects/ralph
cd /home/ubuntu/projects/ralph
echo "Setting up virtual environment..."
/home/ubuntu/.python/bin//python3.8 -m venv venv_ralph
echo "Setting up virtual environment finished."

# Installing requirements
. /home/ubuntu/projects/ralph/venv_ralph/bin/activate
pip install -r /home/ubuntu/projects/ralph/requirements.txt


# Starting new session
tmux new-session -s ralph -d
tmux send-keys -t ralph:1 " cd projects/ralph && cls && python main.py" Enter
tmux new-window
tmux send-keys -t ralph:2 " cd projects/ralph && cls && python scheduler.py" Enter
