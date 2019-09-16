from setuptools import setup, find_packages

setup(
    name='pkg_new_version',
    version='1.0.0',
    author='Harald von Waldow',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.5',
    install_requires=['ckanapi'],
    entry_points={
        'console_scripts': [
            'pkg_new_version = pkg_new_version.pkg_new_version:main',
        ],
    },
)
    
