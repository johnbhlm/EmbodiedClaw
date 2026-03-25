from setuptools import find_packages, setup

package_name = 'embodiedclaw_provider_adapters'

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
    description='Observe/navigate adapter action servers backed by provider abstractions',
    license='TBD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'observe_adapter_server = embodiedclaw_provider_adapters.observe_adapter_server:main',
            'navigate_adapter_server = embodiedclaw_provider_adapters.navigate_adapter_server:main',
            'adapter_launcher = embodiedclaw_provider_adapters.adapter_launcher:main',
        ],
    },
)
