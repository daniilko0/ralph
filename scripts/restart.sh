#!/bin/sh

# Installing requirements
pip install -r requirements.txt


# Starting new session
tmux new-session -s ralph -d
tmux send-keys -t ralph:1 " cd projects/ralph && cls && python main.py" Enter
tmux new-window
tmux send-keys -t ralph:2 " cd projects/ralph && cls && python scheduler.py" Enter
