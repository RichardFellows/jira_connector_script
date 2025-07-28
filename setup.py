#!/usr/bin/env python3
"""
Setup configuration for JIRA Analytics Package
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "JIRA Server Data Extractor and Analytics Dashboard"

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "requests>=2.28.0",
            "duckdb>=0.8.0",
            "marimo>=0.8.0",
            "plotly>=5.17.0",
            "pandas>=2.0.0"
        ]

setup(
    name="jira-analytics",
    version="1.0.0",
    author="JIRA Analytics Team",
    author_email="analytics@company.com",
    description="JIRA Server data extraction and analytics dashboard for agile teams",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/company/jira-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Bug Tracking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ]
    },
    entry_points={
        "console_scripts": [
            "jira-extract=jira_extractor:main",
            "jira-analytics=jira_analytics_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.py"],
    },
    data_files=[
        ("config", ["config.json.example"]),
    ],
    project_urls={
        "Bug Reports": "https://github.com/company/jira-analytics/issues",
        "Source": "https://github.com/company/jira-analytics",
        "Documentation": "https://github.com/company/jira-analytics/wiki",
    },
)