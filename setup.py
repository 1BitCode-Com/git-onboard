#!/usr/bin/env python3
"""
Setup script for Git Onboard
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="git-onboard",
    version="1.0.0",
    author="1BitCode-Com",
    author_email="contact@1bitcode.com",
    description="Automate onboarding of local project folders to GitHub with intelligent recovery capabilities",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/1BitCode-Com/git-onboard",
    packages=find_packages(),
    py_modules=["git_onboard"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",

        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "git-onboard=git_onboard:main",
        ],
    },
    keywords="git, github, automation, onboarding, repository, cli",
    project_urls={
        "Bug Reports": "https://github.com/1BitCode-Com/git-onboard/issues",
        "Source": "https://github.com/1BitCode-Com/git-onboard",
        "Documentation": "https://github.com/1BitCode-Com/git-onboard#readme",
    },
) 