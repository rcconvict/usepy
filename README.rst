Python Usenet Indexer
=====================

:Author: convict
:Version: pre-alpha

Requirements:
------------
- Python 2.7
- Ubuntu 12.04 (Should work with 13.04 as well)
- MySQL
- python-dateutil and python-mysqldb
- Heavy knowledge of mysql, python, and usenet

.. Note:: This is very alpha and should be not used by anyone unless you know what you are doing or want to tinker.

Installation:
-------------
- sudo apt-get install python-dateutil python-mysqldb mysql-server -y
- git clone https://github.com/rcconvict/usepy.git
- cd usepy && python setup.py
- use control.py to activate and de-activate groups
- update_binaries.py and update_releases.py should be self explanatory.
