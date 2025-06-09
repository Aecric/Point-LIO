import os

from launch import LaunchDescription
from launch.actions import GroupAction, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Declare the RViz argument
    mid360_dev = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('livox_ros_driver2'), 'launch'),
            '/msg_MID360_launch.py'])
    )



     # 参数声明
    slam_arg = DeclareLaunchArgument( 
        'slam', 
        default_value='true',
        description='Enable/disable SLAM mode'
    )

    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Flag to launch RViz.')

    save_map_path = DeclareLaunchArgument(
        'save_map_path',
        default_value=os.path.join(
            get_package_share_directory('point_lio'), 'PCD'),
        description='Path to save map.'
    )
    save_map_name = DeclareLaunchArgument(
        'save_map_name',
        default_value='map.pcd',
        description='Name of map to save.'
    )
    pcd_save_en = DeclareLaunchArgument(
        'pcd_save_en',
        default_value='true',
        description='Enable/disable pcd save.'
    )    

    # Node parameters, including those from the YAML configuration file
    laser_mapping_params = [
        PathJoinSubstitution([
            FindPackageShare('point_lio'),
            'config', 'mid360.yaml'
        ]),
        {
            'slam': LaunchConfiguration('slam'),  # 参数绑定

            'use_imu_as_input': False,  # Change to True to use IMU as input of Point-LIO
            'prop_at_freq_of_imu': True,
            'check_satu': True,
            'init_map_size': 10,
            'point_filter_num': 3,  # Options: 1, 3
            'space_down_sample': True,
            'filter_size_surf': 0.1,  # Options: 0.5, 0.3, 0.2, 0.15, 0.1
            'filter_size_map': 0.1,  # Options: 0.5, 0.3, 0.15, 0.1
            'ivox_nearby_type': 6,   # Options: 0, 6, 18, 26
            'runtime_pos_log_enable': False,  # Option: True
            'pcd_save.pcd_save_en': LaunchConfiguration('pcd_save_en'),
            'pcd_save.path': LaunchConfiguration('save_map_path'),
            'pcd_save.name': LaunchConfiguration('save_map_name'),
        }
    ]

    # Node definition for laserMapping with Point-LIO
    laser_mapping_node = Node(
        package='point_lio',
        executable='pointlio_mapping',
        name='laserMapping',
        output='screen',
        parameters=laser_mapping_params,
    )

    # Conditional RViz node launch
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('point_lio'),
            'rviz_cfg', 'loam_livox.rviz'
        ])],
        condition=IfCondition(LaunchConfiguration('rviz')),
        prefix='nice'
    )


    tf2_base_link = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='aft_to_base_broadcaster',
        arguments=[
            '--yaw', '0.0', '--pitch', '-0.605', '--roll', '0.0',
            '--x', '-0.49350126', '--y', '0', '--z', '-0.34125725',
            '--frame-id', 'aft_mapped', '--child-frame-id', "base_link"
        ]
    )

    # Assemble the launch description
    ld = LaunchDescription([

        slam_arg,  # 声明参数
        save_map_path,
        save_map_name,
        pcd_save_en,
        # rviz_arg,
        # mid360_dev,
        laser_mapping_node,
        tf2_base_link
        # GroupAction(
        #     actions=[rviz_node],
        #     condition=IfCondition(LaunchConfiguration('rviz'))
        # ),
    ])

    return ld
