#!/bin/bash

# Sentinel Robotics - Launch AWS RoboMaker warehouse world and spawn TurtleBot3 Waffle

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
echo "Starting warehouse world, robot_state_publisher, TurtleBot3 Waffle, and Navigation2..."

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
}

launch_in_terminal "Gazebo - AWS RoboMaker Warehouse" \
    "export TURTLEBOT3_MODEL=waffle; ros2 launch aws_robomaker_small_warehouse_world no_roof_small_warehouse.launch.py"

launch_in_terminal "TurtleBot3 Robot State Publisher" \
    "export TURTLEBOT3_MODEL=waffle; sleep 2; ros2 launch turtlebot3_gazebo robot_state_publisher.launch.py use_sim_time:=True"

launch_in_terminal "Gazebo - Spawn TurtleBot3 Waffle" \
    "export TURTLEBOT3_MODEL=waffle; sleep 5; ros2 launch turtlebot3_gazebo spawn_turtlebot3.launch.py x_pose:=-3.7138 y_pose:=-0.7023"

launch_in_terminal "Navigation2" \
    "export TURTLEBOT3_MODEL=waffle; sleep 8; ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=\$HOME/aws_warehouse_ws/aws_warehouse_map.yaml"

echo "Warehouse world launch requested. robot_state_publisher starts after 2 seconds."
echo "Waffle will spawn after 5 seconds."
echo "Navigation2 will start after 8 seconds."
echo "Note: spawn_turtlebot3.launch.py supports x/y only, so yaw is not applied in this version."
