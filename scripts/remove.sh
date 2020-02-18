#!/bin/sh

# Stop tmux's session
tmux kill-session

# Delete all ralph's contain except .envrc
sudo rm -rf `ls | grep -v ".envrc"`
echo "Folder with project deleted."