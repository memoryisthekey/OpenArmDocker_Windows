#!/usr/bin/env bash
set -e

WS=/home/ros/ros2_ws

# Source base ROS
source /opt/ros/humble/setup.bash

# Build if workspace exists
if [ -d "$WS/src" ] && [ -n "$(ls -A "$WS/src" 2>/dev/null)" ]; then
  echo "Building workspace at $WS ..."
  cd "$WS"
  colcon build
else
  echo "No packages in $WS/src — skipping build."
fi

echo "Workspace setup complete. Source the workspace with 'source ~/.bashrc'"


#echo "Setting up can0 interface..."
#openarm-can-configure-socketcan can0 -fd -b 1000000 -d 5000000

#echo "Setting up can1 interface..."
#openarm-can-configure-socketcan can1 -fd -b 1000000 -d 5000000

exec bash