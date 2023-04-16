#
#    This file is part of the Pi Entertainment System (PES).
#
#    PES provides an interactive GUI for games console emulators
#    and is designed to work on the Raspberry Pi.
#
#    Copyright (C) 2020-2023 Neil Munday (neil@mundayweb.com)
#
#    PES is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PES is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PES.  If not, see <http://www.gnu.org/licenses/>.
#

"""
PES GUI set-up
"""

# standard imports
import pathlib
import sys

# third-party imports
import setuptools

# PES imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0] / "src"))
from pes import VERSION_ARCH, VERSION_AUTHOR, VERSION_NUMBER # pylint: disable=wrong-import-position

setuptools.setup(
    author=VERSION_AUTHOR,
    description='GUI package for PES written in PyQT',
    entry_points = {
        'console_scripts': [
            'pes-gui=pes.main:pes_main',
        ],
    },
    extras_require={
        'web': ['Flask', 'waitress']
    },
    include_package_data=True,
    install_requires=[
        'PyQt5',
        'PySDL2',
        'setuptools'
    ],
    license='GPLv3',
    long_description='The Pi Entertainment System (PES) GUI',
    maintainer=VERSION_AUTHOR,
    name='pes-gui',
    packages=setuptools.find_namespace_packages(where='src'),
    package_dir={'': 'src'},
    platforms=VERSION_ARCH,
    python_requires='>=3.6',
    scripts=['bin/pes'],
    url='https://github.com/Pi-Entertainment-System/pes-gui',
    version=VERSION_NUMBER
)
