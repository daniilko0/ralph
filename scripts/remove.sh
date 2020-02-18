#!/bin/sh

# Stop tmux's session
tmux kill-session

# Delete all ralph's contain except .envrc
rm -r `ls | grep -v ".envrc"`
echo "Folder with project deleted."