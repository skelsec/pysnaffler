# pySnaffler

Snaffler, but in Python

# Important info
This project is a Python version of the well-known [Snaffler](https://github.com/SnaffCon/Snaffler) project. Not a full implementation of that project, only focusing on SMB share/dir/file enumeration and download and parse. Read: no LDAP etc.  
It contains the default classifiers (referred to as `ruleset` in pySnaffler) baked-in already but this ruleset is a part of Snaffler project.
Snaffler's author's Twitter: @mikeloss and @sh3r4_hax  

# Project info
The project is fully compatible with the TOML based rulesets from the original Snaffler project, the SMB connectivity is based on the [aiosmb](https://github.com/skelsec/aiosmb) library. Note: the Snaffler's core config file is NOT compatible with this project.
