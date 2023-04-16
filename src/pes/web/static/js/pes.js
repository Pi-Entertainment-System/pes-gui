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

function play(id) {
    $.get(
        "/play", { id: id}
    ).done(function(data) {
        var j = JSON.parse(data);
        if (j.result) {
            bootbox.alert({
                title: "Loading",
                message: "Your game is now loading on your device."
            });
        }
        else {
            bootbox.alert({
                title: "Failure",
                message: j.msg
            });
        }
    });
}

function poweroff() {
    bootbox.confirm({
        title: "Power Off",
        message: "Are you sure you want to shutdown your PES system?",
        callback: function(result) {
            if (result) {
                $.get(
                    "/shutdown"
                ).done(function(data){

                });
            }
        }
    })
}

function reboot() {
    bootbox.confirm({
        title: "Reboot",
        message: "Are you sure you want to reboot your PES system?",
        callback: function(result) {
            if (result) {
                $.get(
                    "/reboot"
                ).done(function(data){

                });
            }
        }
    })
}