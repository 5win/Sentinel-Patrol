#!/bin/bash

# Sentinel Robotics - Launch Gazebo & Navigation2 in separate terminal windows

TERM_CMD=""

if command -v gnome-terminal &> /dev/null; then
    TERM_CMD="gnome-terminal"
elif command -v xterm &> /dev/null; then
    TERM_CMD="xterm"
elif command -v konsole &> /dev/null; then
    TERM_CMD="konsole"
else
    echo "No supported terminal emulator found (gnome-terminal, xterm, konsole)"
    exit 1
fi

echo "Using terminal: $TERM_CMD"
echo "Starting Simulation nodes..."

launch_in_terminal() {
    local title="$1"
    local cmd="$2"

    case "$TERM_CMD" in
        gnome-terminal)
            gnome-terminal --title="$title" -- bash -c "$cmd; echo ''; echo '=== Process ended. Press Enter to close ==='; read" &
            ;;
        xterm)
            xterm -title "$title" -e bash -c "$cmd; echo ''; echo '=== Process ended. Press Enter to close ==='; read" &
            ;;
        konsole)
            konsole --title "$title" -e bash -c "$cmd; echo ''; echo '=== Process ended. Press Enter to close ==='; read" &
            ;;
    esac

    sleep 2  # Small delay between launches
}

# 1. Gazebo simulation
launch_in_terminal "Gazebo - TurtleBot3 World" \
    "ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py"

# 2. Navigation2
launch_in_terminal "Navigation2" \
    "ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=\$HOME/waffle_map.yaml"

echo "Simulation nodes launched."
