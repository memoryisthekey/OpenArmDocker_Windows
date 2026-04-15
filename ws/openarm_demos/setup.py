from setuptools import find_packages, setup

package_name = 'openarm_demos'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rno',
    maintainer_email='rno@mmmi.sdu.dk',
    description='Demo nodes for OpenArm',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'dual_wave_demo = openarm_demos.dual_wave_demo:main',
            'handshake_demo = openarm_demos.handshake_demo:main',
        ],
    },
)
