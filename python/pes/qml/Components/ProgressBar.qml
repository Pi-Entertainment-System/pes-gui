import QtQuick 2.7
import "../Style/" 1.0

Rectangle {
	color: Colour.progressBarBg
	property int indent: 3
	property real progress: 0

	Rectangle {
		x: parent.indent
		y: parent.indent
		height: parent.height - (parent.indent * 2)
		width: (parent.width - (parent.indent * 2)) * progress
		color: Colour.progressBar
	}
}
