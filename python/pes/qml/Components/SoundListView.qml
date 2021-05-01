/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2021 Neil Munday (neil@mundayweb.com)

    PES is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PES is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PES.  If not, see <http://www.gnu.org/licenses/>.
*/

import QtQuick 2.7
import QtQuick.Layouts 1.12
import QtQuick.Controls 2.5
import QtMultimedia 5.12
import "../Style/" 1.0

ListView {
    id: listView

    property QtObject navSound: null;
    property bool soundOn: true;

    signal itemHighlighted(variant item);

    Keys.onDownPressed: {
        if (currentIndex < count - 1) {
            if (navSound && soundOn) {
                navSound.play();

            }
            currentIndex += 1;
            itemHighlighted(model.get(currentIndex));
        }
    }
    Keys.onUpPressed: {
        if (currentIndex > 0) {
            if (navSound && soundOn) {
                navSound.play();
            }
            currentIndex -= 1;
            itemHighlighted(model.get(currentIndex));
        }
    }

    onActiveFocusChanged: {
        if (activeFocus && visible && currentIndex >= 0 && currentIndex < count && navSound && soundOn) {
            navSound.play();
        }
    }
}