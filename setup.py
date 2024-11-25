from setuptools import setup, find_packages

# Read README.md for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pretty_pie_log",
    version="0.3.11",
    author="chanpreet3000",
    author_email="chanpreet3000@gmail.com",
    description="A feature-rich logging utility that provides colorized console output with customizable formatting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chanpreet3000/pretty-pie-log",
    project_urls={
        "Bug Tracker": "https://github.com/chanpreet3000/pretty-pie-log/issues",
        "Source Code": "https://github.com/chanpreet3000/pretty-pie-log",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "colorama>=0.4.6",
        "pytz>=2024.2"
    ],
    keywords=[
        "logging",
        "colorized",
        "console",
        "debug",
        "formatting",
        "pretty-print",
        "thread-safe",
        "timezone",
        "structured-logging"
    ],
    package_data={
        "pretty_pie_log": ["py.typed"],  # Include type information
    },
    include_package_data=True,
)