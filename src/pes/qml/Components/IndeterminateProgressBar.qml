/*
    This file is part of the Pi Entertainment System (PES).

    PES provides an interactive GUI for games console emulators
    and is designed to work on the Raspberry Pi.

    Copyright (C) 2020-2023 Neil Munday (neil@mundayweb.com)

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
	id: pb
	color: Colour.progressBarBg
	property int indent: 3
	property real progress: 0

	Rectangle {
		x: pb.indent
		y: pb.indent
		id: bar
		color: Colour.progressBar
    width: 400
		height: pb.height - (pb.indent * 2)

		XAnimator on x {
			id: animation
	  	from: 0
			to: 1
			duration: 3000
	    loops: Animation.Infinite
	    running: false
	  }
	}
  onWidthChanged: {
		console.error("x: " + pb.x + ", width: " + pb.width);
		animation.to = pb.width - bar.width;
		if (visible) {
			animation.running = true;
		}
	}
	onVisibleChanged: {
		if (visible) {
			animation.running = pb.indeterminate;
		}
		else {
			animation.running = false;
		}
	}
}
