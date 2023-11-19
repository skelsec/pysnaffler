import re

from setuptools import setup, find_packages

VERSIONFILE = "pysnaffler/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
if mo := re.search(VSRE, verstrline, re.M):
    verstr = mo[1]
else:
    raise RuntimeError(f"Unable to find version string in {VERSIONFILE}.")

setup(
    # Application name:
    name="pysnaffler",

    # Version number (initial):
    version=verstr,

    # Application author details:
    author="Tamas Jos",
    author_email="info@skelsecprojects.com",

    # Packages
    packages=find_packages(),

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://github.com/skelsec/pysnaffler",

    zip_safe=False,
    #
    # license="LICENSE.txt",
    description="Snaffler. But in python.",

    # long_description=open("README.txt").read(),
    python_requires='>=3.7',
    install_requires=[
        'aiosmb>=0.4.7',
        'toml',
    ],

    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'pysnaffler = pysnaffler.__main__:main',
            'pysnaffler-whatif = pysnaffler.whatif:main'
        ],

    }
)
