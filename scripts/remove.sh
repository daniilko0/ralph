#!/bin/sh

# Stop tmux's session
tmux kill-server

# Delete all ralph's contain
rm -rf /home/ubuntu/projects/ralph/*
echo "Folder with project deleted."