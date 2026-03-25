from setuptools import find_packages, setup

package_name = 'embodiedclaw_skill_servers'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='EmbodiedClaw',
    maintainer_email='dev@example.com',
    description='Fake skill action servers for EmbodiedClaw',
    license='TBD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fake_navigate_server = embodiedclaw_skill_servers.fake_navigate_server:main',
            'fake_manipulate_server = embodiedclaw_skill_servers.fake_manipulate_server:main',
            'fake_inspect_server = embodiedclaw_skill_servers.fake_inspect_server:main',
            'skill_launcher = embodiedclaw_skill_servers.skill_launcher:main',
        ],
    },
)
