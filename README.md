# Pi Entertainment System (PES) GUI

[![GitHub stars](https://img.shields.io/github/stars/Pi-Entertainment-System/pes-gui)](https://github.com/Pi-Entertainment-System/pes-gui/stargazers) [![GitHub issues](https://img.shields.io/github/issues/Pi-Entertainment-System/pes-gui)](https://github.com/Pi-Entertainment-System/pes-gui/issues) ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Pi-Entertainment-System/pes-gui/pylint.yml?label=PyLint) [![GitHub license](https://img.shields.io/github/license/Pi-Entertainment-System/pes-gui)](https://github.com/Pi-Entertainment-System/pes-gui/blob/main/LICENSE)

PES is a graphical front end for a variety of games console emulators that has been written in [Python](https://www.python.org>) which is intended for use on the Raspberry Pi.

At the heart of PES is the PES GUI. This can be used on any OS that supports [Python3](https://www.python.org>), [PySDL2](http://pysdl2.readthedocs.org/>) and [PyQT5](https://riverbankcomputing.com/software/pyqt).

Prior to version 3.0, PES and its supporting build scripts for the emulators etc. were provided under one single repository. As of version 3.0 it was decided to split the PES project into a separate repositories to aid maintainability.

Please see the [pes-setup](https://github.com/Pi-Entertainment-System/pes-setup) for the scripts and instructions for setting up your Raspberry Pi build environment.

The [pes-packages](https://github.com/Pi-Entertainment-System/pes-packages) repository contains the Arch Linux package build files to all off the Arch Linux packages required by PES that are not already provided by Arch Linux.

# Requirements

- Flask
- QT5
- PyQT5
- PySDL2
- SDL2
- [rasum](https://github.com/Pi-Entertainment-System/rasum)
- waitress

# Creating the PES database

PES requires its database to be populated with theGamesDB and RetroAchievements.org data.

Once you have cloned this repository you can create the database like so:

```
export PYTHONPATH=src/pes
bin/populate-db.py -g -m -d data -r --match -v
```

# Load GUI

```
bin/pes
```

# Acknowledgements

* GUI sound effects provided by: [Octave](https://github.com/scopegate/octave)
* Icons provided by: [Game-Icons.net](https://game-icons.net)
