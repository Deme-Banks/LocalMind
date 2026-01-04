"""
Setup script for LocalMind
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="localmind",
    version="1.0.0",
    description="A lightweight, privacy-focused local AI that runs fully on your computer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="LocalMind Contributors",
    author_email="",
    url="https://github.com/Deme-Banks/LocalMind",
    packages=find_packages(exclude=["tests", "tests.*", "venv", "venv.*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.0",
        ],
        "gguf": [
            "llama-cpp-python>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "localmind=src.cli.interface:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai, machine-learning, local-ai, privacy, ollama, transformers, llm",
    include_package_data=True,
    zip_safe=False,
)

