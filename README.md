# VOC-automation
List of folders and what they do?
- 'calui'

    Graphic user interface for Calibration, both droplet and gas tank experiments
- 'jupyter'

    Analysis of calibration data
- 'SAM' 

    Validation test bed control code
- 'move'

    Move and unzip data during desired time period from analyzer to desired location
    This script only uses Python3 default packages, no need to install any libraries, and it can be used on any analyzer.

Features:
- Python 3.9
- PyQt6
- Tested on Windows, Mac and Linux

Requirement:
- There are a long list of files and libraries needed to make it work.
    Please run calui/t5module.py to find out what you need, and install whatever is missing.
    As long as you have Picarro's internet access, there should be no error.
    MFC control code requires a USB cable connected to computer.
- Mongo is needed
- I run most scripts locally on my computer

How to use: run scrips in terminal
- calui: t8ui.py
- jupyter: jupy.py
- SAM: t7.py
- move: t5.py
