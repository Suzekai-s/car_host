# car_host — 桌面主机（SLAM 建图 / 导航 / RViz）

部署在桌面计算机上（WSL2 / Linux 主机），接收车载上位机 `car_agent` 的传感器数据，运行 SLAM 建图、自主导航和可视化。

## 系统架构

```
car_agent（车载上位机）                car_host（桌面主机）
┌──────────────────┐                 ┌──────────────────────────┐
│  lslidar_driver  │  ──DDS──▶ /scan │  slam_toolbox            │
│  v4l2_camera     │  ──DDS──▶       │  （同步定位与建图）       │
│  serial_bridge   │  ──DDS──▶ /odom │                          │
│                  │         + tf    │  Nav2 导航栈              │
│  cmd_vel_relay   │  ◀──DDS──       │  ├── map_server          │
│                  │  /cmd_vel       │  ├── AMCL（定位）        │
│                  │                 │  ├── global_planner      │
│                  │                 │  ├── local_planner       │
│                  │                 │  └── controller          │
│                  │                 │                          │
│                  │                 │  RViz2                   │
│                  │                 │  （3D 可视化）           │
└──────────────────┘                 └──────────────────────────┘
```

## 目录结构

```
car_host/
├── setup.sh                        # 环境初始化（只需跑一次）
├── colcon_host.sh                  # 一键编译
├── config/
│   └── cyclonedds_car.xml          # CycloneDDS 网络配置（单播直连）
│
└── src/
    └── car_host_bringup/           # 启动文件 + 配置
        ├── launch/car_host.launch.py
        ├── config/
        │   ├── slam_toolbox.yaml   #    SLAM 参数
        │   └── nav2_params.yaml    #    导航栈参数
        └── rviz/
            ├── car_slam.rviz       #    建图 RViz 配置
            └── car_nav.rviz        #    导航 RViz 配置
```

## 节点详解

### 1. SLAM Toolbox（`sync_slam_toolbox_node`）

实时同步定位与建图。

| 参数 | 值 |
|------|-----|
| 地图帧 | `map` |
| 里程计帧 | `odom` |
| 基础帧 | `base_link` |
| 扫描话题 | `/scan`（最大范围 12m） |
| 建图模式 | `mapping`（在线建图）/ `localization`（定位模式） |
| 回环检测 | 开启（最小链长 10，最大方差 3.0） |
| 求解器 | Ceres + SPARSE_NORMAL_CHOLESKY |
| 地图分辨率 | 0.05m |
| 地图更新间隔 | 1.0s |

**切换定位模式**：修改 `slam_toolbox.yaml` 中的 `mode: "localization"`。

### 2. Nav2 导航栈

完整的前端规划 + 后端控制导航堆栈。

| 组件 | 说明 |
|------|------|
| map_server | 加载已保存的地图（YAML + PNG） |
| AMCL | 自适应蒙特卡洛定位，500-2000 粒子 |
| global_planner | Navfn 全局路径规划 |
| controller | RegulatedPurePursuit 控制器 |
| global_costmap | 静态层 + 障碍物层 + 膨胀层 |
| local_costmap | 障碍物层 + 膨胀层，滚动窗口 3×3m |
| bt_navigator | 行为树导航，/odom 话题超时 20s |

**运动学参数**（`nav2_params.yaml`）：

| 参数 | 值 |
|------|-----|
| 最大线速度 | 0.5 m/s |
| 最大角速度 | 0.5 rad/s |
| 最大加速度 | 0.5 m/s² |
| 最大角加速度 | 0.5 rad/s² |
| 机器人半径 | 0.25 m |
| 膨胀半径 | 0.3 m |
| 控制前瞻距离 | 0.4 m |

### 3. RViz2 可视化

两种 RViz 预设配置：

| 配置 | 用途 | 显示内容 |
|------|------|---------|
| `car_slam.rviz` | 建图 | Grid + TF + LaserScan + Map |
| `car_nav.rviz` | 导航 | 上述 + AMCL 粒子 + 全局/局部路径 + Costmap |

## 环境搭建

### 前置条件

- **WSL2**（推荐）或原生 Linux 桌面
- ROS 2 **Humble**（已安装）
- `car_agent` 已在车上正常运行

### 首次初始化

```bash
cd ~/workspace/car_host
bash setup.sh
```

脚本自动完成：安装依赖（SLAM / Nav2 / RViz）→ 配置 DDS 环境变量 → 编译。

### 手动分步

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y \
  ros-humble-slam-toolbox \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-rmw-cyclonedds-cpp \
  ros-humble-rviz2

# 2. DDS 环境变量
echo -e '\nexport RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\nexport ROS_DOMAIN_ID=42\nexport ROS_LOCALHOST_ONLY=0' >> ~/.bashrc
source ~/.bashrc

# 3. 配置 CycloneDDS 单播直连
#    编辑 config/cyclonedds_car.xml
#    将 <Peer address="..."> 改为上位机的实际 IP

# 4. 编译
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 使用方式

### 每日启动流程

```bash
# 1. 加载环境（如果已加到 bashrc 则跳过）
source ~/workspace/car_distributed/car_host/install/setup.bash

# 2. 确认能看到上位机话题
ros2 daemon stop
ros2 topic list --no-daemon
# 应看到 /scan /odom /tf /car/cmd_vel ...

# 3. 选任务启动：

# 仅 RViz 可视化
ros2 launch car_host_bringup car_host.launch.py slam:=false nav:=false

# 或 SLAM 建图
# ros2 launch car_host_bringup car_host.launch.py

# 或自主导航
# ros2 launch car_host_bringup car_host.launch.py nav:=true map:=~/car_map.yaml
```

### 免 source 配置

每次新开终端都要重新 source，可以**加到 bashrc 自动加载**：

```bash
echo 'source ~/workspace/car_distributed/car_host/install/setup.bash' >> ~/.bashrc
```

### 第一步：确认通信

确保 `car_agent` 已在车上运行，然后：

```bash
# 设置 CycloneDDS 单播配置
export CYCLONEDDS_URI=file://$HOME/workspace/car_host/config/cyclonedds_car.xml
ros2 topic list --no-daemon
# 预期看到：/scan /odom /tf /car/cmd_vel /camera_info ...
```

> **注意**：如果话题不完整，执行 `ros2 daemon stop` 清除缓存后再试。

### 第二步：RViz 可视化（不建图）

```bash
ros2 launch car_host_bringup car_host.launch.py slam:=false nav:=false
```

### 第三步：SLAM 建图

```bash
ros2 launch car_host_bringup car_host.launch.py
```

操控小车走遍建图区域，观察 RViz 中的地图逐步生成。

### 第四步：保存地图

```bash
ros2 run nav2_map_server map_saver_cli -f ~/car_map
```

会生成 `~/car_map.yaml` + `~/car_map.pgm`。

### 第五步：自主导航

```bash
ros2 launch car_host_bringup car_host.launch.py nav:=true map:=~/car_map.yaml
```

在 RViz 中点击 **2D Goal Pose** 设定目标点，小车将自主导航前往。

## CycloneDDS 网络配置

### 为什么需要 Peers 单播配置

WSL2 镜像网络下存在多个虚拟网卡，CycloneDDS 默认的 UDP 组播可能走错网卡或被代理软件拦截。通过 `Peers` 配置绕过组播，直接单播直连上位机。

### 配置文件

```xml
<!-- config/cyclonedds_car.xml -->
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>192.168.1.40</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <Peers>
        <Peer address="192.168.1.246"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

| 字段 | 说明 | 必须修改 |
|------|------|---------|
| `NetworkInterfaceAddress` | **本机**的局域网 IP | 不一定（IP 变了要改） |
| `Peer address` | **上位机**的局域网 IP | 需要改为你上位机的实际 IP |

```bash
# 使用配置
export CYCLONEDDS_URI=file://$HOME/workspace/car_host/config/cyclonedds_car.xml
# 或添加到 ~/.bashrc 自动加载
```

### 如果 IP 是动态分配的

建议给上位机设置固定局域网 IP，或在 Windows hosts 文件中绑定：
```
192.168.1.246  car-agent
```
然后将配置改为 `<Peer address="car-agent"/>`，这样只改 hosts 一处即可。

## 工作流程

```
┌──────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐
│  建图阶段  │   │  保存地图  │   │  导航阶段  │   │  重定位  │
│          │   │           │   │          │   │          │
│ car_host │   │ map_saver │   │ car_host │   │ 已有地图 │
│ slam:=tr │──▶│ _cli -f   │──▶│ nav:=true│──▶│ 重复使用 │
│ ue       │   │ ~/map     │   │ map=~/ma │   │          │
└──────────┘   └───────────┘   │ p.yaml   │   └──────────┘
                               └──────────┘
```

## 常见问题

**Q：`ros2 topic list` 看不到上位机的话题**
A：按顺序排查：① 上位机正常运行？② 能互相 ping 通？③ Domain ID 一致？④ CycloneDDS 配置中的 IP 正确？⑤ `ros2 daemon stop` 清缓存

**Q：RViz 一片空白**
A：检查左侧 **Fixed Frame** 是否设为 `map`（建图时）或 `odom`（仅可视化时）。没有 odom 数据时可以先用 `laser_link` 看雷达。

**Q：SLAM 建图漂移严重**
A：里程计参数（轮径、减速比等）需要标定。调整 `serial_bridge` 的参数后重启 `car_agent`。

**Q：导航时小车不走**
A：检查 `nav2_params.yaml` 中的 `odom_topic` 是否与上位机发布的 `/odom` 一致。检查 AMCL 是否完成了初始化定位。
