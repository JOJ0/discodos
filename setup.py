from setuptools import setup, find_packages

setup(
    name="discodos",
    version="3.0.2",
    description="DJ and record collector's toolbox for Discogs",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    author="J0J0 Todos",
    url="https://discodos.jojotodos.net",
    project_urls={
        "Bug Tracker": "https://github.com/joj0/discodos/issues",
        "Documentation": "https://discodos.readthedocs.io",
        "Source Code": "https://github.com/joj0/discodos/",
    },
    packages=find_packages(),
    test_suite="tests",
    license="GPLv3+",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Environment :: Console",
    ],
    install_requires=[
        "Click",
        "tabulate",
        "PyYaml",
        "click-option-group",
        "dropbox",
        "musicbrainzngs",
        "rich",
        "textual",
        "python3-discogs-client",
        "webdavclient3",
    ],
    entry_points={
        "console_scripts": [
            "discosync = discodos.cmd.sync:main",
            "dsc = discodos.cmd23:main_cmd",
        ],
    },
    flake8_ignore=["E501", "E225"],
    exclude=[
        ".git",
        "__pycache__",
        "docs/source/conf.py",
        "old",
        "build",
        "dist",
        ".eggs",
        "discodos_logo.py",
    ],
)

