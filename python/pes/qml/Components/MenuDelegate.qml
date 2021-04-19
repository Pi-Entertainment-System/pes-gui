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
import "../Style/" 1.0

Rectangle {
	id: menuDelegateRect
	height: 50
	width: parent.width
	color: focus ? Colour.menuFocus : Colour.menuBg
	property alias text: menuDelegateText.text

	//Keys.onReturnPressed: {
	//	parent.foo(event);
	//}

	Rectangle {
		id: menuDelegateLine
		width: 5
		height: parent.height
		color: Colour.line
		visible: parent.focus
	}

	Text {
		x: menuDelegateLine.x + 8
		id: menuDelegateText
		text: name
		color: parent.focus ? Colour.text : Colour.menuText
		font.pixelSize: FontStyle.menuSize
		font.family: FontStyle.font
	}
}
