#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="psychopy-gaze-tracking",
    version="0.1.0",
    author="PsychoPy Gaze Tracking Team",
    author_email="example@example.com",
    description="A gaze tracking application built with PsychoPy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/PsychoPy_GazeTracking",
    packages=find_packages(include=["PsychoPyInterface", "PsychoPyInterface.*", "GazeAnalytics", "GazeAnalytics.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
    ],
    python_requires=">=3.9",
    install_requires=[
        "psychopy>=2024.2.0",
        "numpy>=1.22.0",
        "pandas>=1.5.0",
        "scipy>=1.9.0",
        "matplotlib>=3.6.0",
        "pillow>=9.0.0",
        "opencv-python>=4.6.0",
        "websockets>=10.0.0",
        "pyglet>=1.5.0",
        "pyyaml>=6.0",
        "pyopengl>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "web": [
            "aiohttp>=3.8.0",
            "python-dotenv>=1.0.0",
            "sqlalchemy>=2.0.0",
            "flask>=2.2.0",
            "flask-cors>=3.0.10",
        ],
    },
    entry_points={
        "console_scripts": [
            "psychopy-gaze-launcher=PsychoPyInterface.launcher:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 