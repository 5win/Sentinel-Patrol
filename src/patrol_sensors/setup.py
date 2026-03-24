from setuptools import find_packages, setup

package_name = 'patrol_sensors'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'rclpy', 'sensor_msgs'],
    zip_safe=True,
    maintainer='sgoh',
    maintainer_email='sgoh@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'scan_logger = patrol_sensors.scan_logger:main',
            'patrol_safety_gate = patrol_sensors.patrol_safety_gate:main'
        ],
    },
)
