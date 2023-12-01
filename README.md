![Supported Python versions](https://img.shields.io/badge/python-3.7+-blue.svg) [![Twitter](https://img.shields.io/twitter/follow/skelsec?label=skelsec&style=social)](https://twitter.com/intent/follow?screen_name=skelsec)

## :triangular_flag_on_post: Sponsors

If you like this project, consider sponsoring it on GitHub! [Sponsors](https://github.com/sponsors/skelsec/)

# pySnaffler

Snaffler, but in Python

# Important info
This project is a Python version of the well-known [Snaffler](https://github.com/SnaffCon/Snaffler) project. Not a full implementation of that project, only focusing on SMB share/dir/file enumeration and download and parse. Read: no LDAP etc.  
It contains the default classifiers (referred to as `ruleset` in pySnaffler) baked-in already but this ruleset is a part of Snaffler project.
Snaffler's author's Twitter: @mikeloss and @sh3r4_hax  

# Project info
The project is fully compatible with the TOML based rulesets from the original Snaffler project, the SMB connectivity is based on the [aiosmb](https://github.com/skelsec/aiosmb) library. Note: the Snaffler's core config file is NOT compatible with this project.

# Usage
Either install it via pip or just clone the project and install `toml` and `aiosmb>=0.4.5`.  
If installed via pip you'll get two executables: 
- `pysnaffler`
- `pysnaffler-whatif` (not tested)
  
Use `pysnaffler -h` to see all parameters.
# Example
- Enumerate `10.10.10.2` using the password credentials of `TEST\victim` user using `NTLM` auth.
`pysnaffler 'smb2+ntlm-password://TEST\victim:Passw0rd!1@10.10.10.2' 10.10.10.2`
  
- Enumerate `10.10.10.2` using the NT credentials of `TEST\victim` user using `NTLM` auth.
`pysnaffler 'smb2+ntlm-nt://TEST\victim:<NThash>@10.10.10.2' 10.10.10.2`
  
- Enumerate `win2019ad.test.corp` using the password credentials of `TEST\victim` user using `KERBEROS` auth.
`pysnaffler 'smb2+kerberos+password://TEST\victim:Passw0rd!1@win2019ad.test.corp/?dc=10.10.10.2' 10.10.10.2`

