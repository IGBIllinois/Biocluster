# module_to_mediawiki

* Scraps the environmental modules for the application name, version, and description
* Sends it to a mediawiki page
* Works with environmental modules, http://modules.sourceforge.net/ and Lmod, https://lmod.readthedocs.io/en/latest/

## Installation

* Create a mediawiki user with api privileges
* Copy config.inc.php.dist to config.inc.php
```
cp config.inc.php.dist config.inc.php
```
* Edit config.inc.php with the mediawiki page, title, mediawiki user and password
* Add to cron script to run every night


