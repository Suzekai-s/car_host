#!/usr/bin/env bash
# 一键编译 car_host (主机/WSL2 工作区)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source /opt/ros/humble/setup.bash
colcon build "$@"
source install/setup.bash

echo ""
echo "[car_host] ✅ 编译完成"
echo "[car_host] SLAM:   ros2 launch car_host_bringup car_host.launch.py"
echo "[car_host] 导航:   ros2 launch car_host_bringup car_host.launch.py nav:=true map:=~/car_map.yaml"
