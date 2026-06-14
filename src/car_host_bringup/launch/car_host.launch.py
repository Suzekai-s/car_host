"""主机（WSL2）启动文件 — SLAM 建图 / 自主导航.

订阅上位机 car_agent 发布的传感器话题，运行高算力任务。

SLAM 建图:
  ros2 launch car_host_bringup car_host.launch.py

自主导航（需要先保存地图）:
  ros2 launch car_host_bringup car_host.launch.py map:=~/car_map.yaml

仅 RViz 可视化（不运行 SLAM/导航）:
  ros2 launch car_host_bringup car_host.launch.py slam:=false nav:=false
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_dir = FindPackageShare("car_host_bringup")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")

    declare_slam = DeclareLaunchArgument("slam", default_value="true", description="启动 SLAM 建图")
    declare_nav = DeclareLaunchArgument("nav", default_value="false", description="启动自主导航")
    declare_map = DeclareLaunchArgument("map", default_value="", description="导航模式：地图文件路径")

    # ── slam_toolbox ──
    slam_node = Node(
        package="slam_toolbox", executable="sync_slam_toolbox_node",
        name="slam_toolbox", output="screen",
        parameters=[PathJoinSubstitution([bringup_dir, "config", "slam_toolbox.yaml"])],
        condition=IfCondition(LaunchConfiguration("slam")),
    )

    # ── 地图服务器 ──
    map_server_node = Node(
        package="nav2_map_server", executable="map_server",
        name="map_server", output="screen",
        parameters=[{"yaml_filename": LaunchConfiguration("map")}],
        condition=IfCondition(LaunchConfiguration("nav")),
    )

    # ── AMCL 定位 ──
    amcl_node = Node(
        package="nav2_amcl", executable="amcl",
        name="amcl", output="screen",
        parameters=[PathJoinSubstitution([bringup_dir, "config", "nav2_params.yaml"])],
        condition=IfCondition(LaunchConfiguration("nav")),
    )

    # ── 生命周期管理器 ──
    lifecycle_node = Node(
        package="nav2_lifecycle_manager", executable="lifecycle_manager",
        name="lifecycle_manager_localization", output="screen",
        parameters=[{"autostart": True, "node_names": ["map_server", "amcl"]}],
        condition=IfCondition(LaunchConfiguration("nav")),
    )

    # ── Nav2 导航栈 ──
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "False",
            "params_file": PathJoinSubstitution([bringup_dir, "config", "nav2_params.yaml"]),
        }.items(),
        condition=IfCondition(LaunchConfiguration("nav")),
    )

    # ── RViz ──
    rviz_config = "car_nav.rviz" if LaunchConfiguration("nav") else "car_slam.rviz"
    rviz_node = Node(
        package="rviz2", executable="rviz2", name="rviz2",
        arguments=["-d", PathJoinSubstitution([bringup_dir, "rviz", "car_slam.rviz"])],
    )

    return LaunchDescription([
        declare_slam, declare_nav, declare_map,
        slam_node,
        map_server_node, amcl_node, lifecycle_node,
        nav2_launch,
        rviz_node,
    ])
