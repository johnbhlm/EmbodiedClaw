from setuptools import find_packages, setup

package_name = 'embodiedclaw_orchestrator'

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
    description='EmbodiedClaw fake task orchestrator node',
    license='TBD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'orchestrator_node = embodiedclaw_orchestrator.orchestrator_node:main',
        ],
    },
)
