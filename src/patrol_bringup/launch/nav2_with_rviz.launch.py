import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    use_composition = LaunchConfiguration('use_composition')
    use_respawn = LaunchConfiguration('use_respawn')
    log_level = LaunchConfiguration('log_level')
    rviz_config = LaunchConfiguration('rviz_config')

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('patrol_bringup'),
                'launch',
                'bringup_launch.py',
            )
        ),
        launch_arguments={
            'namespace': namespace,
            'use_namespace': 'True',
            'map': map_yaml,
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'autostart': autostart,
            'use_composition': use_composition,
            'use_respawn': use_respawn,
            'log_level': log_level,
        }.items(),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('/initialpose', [namespace, '/initialpose']),
            ('/goal_pose', [namespace, '/goal_pose']),
            ('/scan', [namespace, '/scan']),
            ('/map', [namespace, '/map']),
            ('/map_updates', [namespace, '/map_updates']),
            ('/particle_cloud', [namespace, '/particle_cloud']),
            ('/global_costmap/costmap', [namespace, '/global_costmap/costmap']),
            ('/global_costmap/costmap_updates', [namespace, '/global_costmap/costmap_updates']),
            ('/global_costmap/published_footprint', [namespace, '/global_costmap/published_footprint']),
            ('/global_costmap/voxel_marked_cloud', [namespace, '/global_costmap/voxel_marked_cloud']),
            ('/local_costmap/costmap', [namespace, '/local_costmap/costmap']),
            ('/local_costmap/costmap_updates', [namespace, '/local_costmap/costmap_updates']),
            ('/local_costmap/published_footprint', [namespace, '/local_costmap/published_footprint']),
            ('/local_costmap/voxel_marked_cloud', [namespace, '/local_costmap/voxel_marked_cloud']),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='patrol_1'),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                get_package_share_directory('patrol_bringup'),
                'params',
                'nav2_patrol_1_params_humble.yaml',
            ),
        ),
        DeclareLaunchArgument('map', default_value=''),
        DeclareLaunchArgument('use_sim_time', default_value='True'),
        DeclareLaunchArgument('autostart', default_value='True'),
        DeclareLaunchArgument('use_composition', default_value='True'),
        DeclareLaunchArgument('use_respawn', default_value='False'),
        DeclareLaunchArgument('log_level', default_value='info'),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(
                get_package_share_directory('patrol_bringup'),
                'rviz',
                'tb3_navigation2.rviz',
            ),
        ),
        bringup_launch,
        rviz_node,
    ])
