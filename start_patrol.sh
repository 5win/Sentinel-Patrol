#!/bin/bash

# Sentinel Robotics - Launch Patrol nodes in separate terminal windows

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
echo "Starting Patrol nodes..."

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

# 1. Scan Logger
launch_in_terminal "Scan Logger" \
    "ros2 run patrol_sensors scan_logger"

# 2. Patrol Safety Gate
launch_in_terminal "Patrol Safety Gate" \
    "ros2 run patrol_sensors patrol_safety_gate"

# 3. Patrol Manager
launch_in_terminal "Patrol Manager" \
    "ros2 run patrol_manager patrol_manager"

echo "Patrol nodes launched."
