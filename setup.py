#!/usr/bin/env python3
"""Setup script for Mouse Disc"""
from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements = Path("requirements.txt").read_text().strip().split("\n")

setup(
    name="mouse-disc",
    version="1.0.0",
    description="Radial menu for Hyprland with quick shortcuts",
    author="Mouse Disc Team",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mouse-disc=main:main",
        ],
    },
    data_files=[
        ("share/applications", ["mouse-disc.desktop"]),
    ],
    python_requires=">=3.9",
)
