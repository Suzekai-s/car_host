import os
from glob import glob
from setuptools import find_packages, setup

package_name = "car_host_bringup"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@example.com",
    description="Car host: SLAM, Nav2, RViz visualization",
    license="Apache-2.0",
    entry_points={"console_scripts": []},
)
