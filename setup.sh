#!/usr/bin/env bash
# car_host 环境初始化脚本（在 WSL2/主机上只跑一次）

set -e

echo "========================================"
echo " car_host — 主机环境初始化"
echo "========================================"

# 1. 安装系统依赖
echo ""
echo "[1/3] 安装 ROS2 依赖包..."
sudo apt update
sudo apt install -y \
  ros-humble-slam-toolbox \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-nav2-bringup \
  ros-humble-rmw-cyclonedds-cpp \
  ros-humble-rviz2

# 2. 设置 DDS 环境变量
echo ""
echo "[2/3] 配置 DDS 网络环境..."
if ! grep -q "ROS_DOMAIN_ID=42" ~/.bashrc; then
    echo -e '\nexport RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\nexport ROS_DOMAIN_ID=42\nexport ROS_LOCALHOST_ONLY=0' >> ~/.bashrc
    echo "  已添加到 ~/.bashrc"
else
    echo "  已存在，跳过"
fi

# 3. 编译
echo ""
echo "[3/3] 编译 car_host..."
bash colcon_host.sh

echo ""
echo "========================================"
echo "✅ 初始化完成！"
echo "启动: source setup.bash"
echo "SLAM:  ros2 launch car_host_bringup car_host.launch.py"
echo "导航:  ros2 launch car_host_bringup car_host.launch.py nav:=true map:=~/car_map.yaml"
echo "========================================"
