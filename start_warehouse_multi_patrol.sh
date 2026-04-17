#!/bin/bash

# Sentinel Robotics - Launch AWS RoboMaker warehouse world and multi-robot patrol

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
echo "Starting warehouse world and multi-robot patrol..."

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

launch_in_terminal "Patrol - Multi Robot" \
    "export TURTLEBOT3_MODEL=waffle; sleep 3; ros2 launch patrol_bringup multi_patrol.launch.py use_sim_time:=True"

launch_in_terminal "Nav2 + RViz - patrol_1" \
    "export TURTLEBOT3_MODEL=waffle; sleep 8; ros2 launch patrol_bringup nav2_with_rviz.launch.py namespace:=patrol_1 use_sim_time:=True map:=\$HOME/aws_warehouse_ws/aws_warehouse_map.yaml params_file:=\$HOME/robotics/sentinel_patrol/src/patrol_bringup/params/nav2_patrol_1_params_humble.yaml"

launch_in_terminal "Nav2 + RViz - patrol_2" \
    "export TURTLEBOT3_MODEL=waffle; sleep 10; ros2 launch patrol_bringup nav2_with_rviz.launch.py namespace:=patrol_2 use_sim_time:=True map:=\$HOME/aws_warehouse_ws/aws_warehouse_map.yaml params_file:=\$HOME/robotics/sentinel_patrol/src/patrol_bringup/params/nav2_patrol_2_params_humble.yaml"

echo "Warehouse world launch requested."
echo "Multi-robot patrol will start after 3 seconds."
echo "Nav2 + RViz for patrol_1 will start after 8 seconds."
echo "Nav2 + RViz for patrol_2 will start after 10 seconds."
