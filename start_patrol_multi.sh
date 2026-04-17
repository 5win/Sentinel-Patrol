#!/bin/bash

# Sentinel Robotics - Launch Patrol nodes for patrol_1 and patrol_2 in separate terminal windows

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAYPOINTS_FILE="$PROJECT_DIR/src/patrol_manager/config/waypoints.yaml"

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
echo "Starting Patrol nodes for /patrol_1 and /patrol_2..."

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
            konsole --title="$title" -e bash -c "$cmd; echo ''; echo '=== Process ended. Press Enter to close ==='; read" &
            ;;
    esac

    sleep 2
}

# patrol_1
launch_in_terminal "Scan Logger - patrol_1" \
    "ros2 run patrol_sensors scan_logger --ros-args -r __ns:=/patrol_1 -p use_sim_time:=True"

launch_in_terminal "Patrol Safety Gate - patrol_1" \
    "ros2 run patrol_sensors patrol_safety_gate --ros-args -r __ns:=/patrol_1 -p use_sim_time:=True"

launch_in_terminal "Patrol Manager - patrol_1" \
    "ros2 run patrol_manager patrol_manager --ros-args -r __ns:=/patrol_1 -p use_sim_time:=True -p waypoints_file:=$WAYPOINTS_FILE"

# patrol_2
launch_in_terminal "Scan Logger - patrol_2" \
    "ros2 run patrol_sensors scan_logger --ros-args -r __ns:=/patrol_2 -p use_sim_time:=True"

launch_in_terminal "Patrol Safety Gate - patrol_2" \
    "ros2 run patrol_sensors patrol_safety_gate --ros-args -r __ns:=/patrol_2 -p use_sim_time:=True"

launch_in_terminal "Patrol Manager - patrol_2" \
    "ros2 run patrol_manager patrol_manager --ros-args -r __ns:=/patrol_2 -p use_sim_time:=True -p waypoints_file:=$WAYPOINTS_FILE"

echo "Patrol nodes launched for /patrol_1 and /patrol_2."
