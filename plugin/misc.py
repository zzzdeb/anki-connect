# Copyright 2016-2020 Alex Yatskov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from . import util


@util.api()
def version():
    return util.setting('apiVersion')


@util.api()
def sync():
    util.window().onSync()


@util.api()
def loadProfile(name):
    if name not in util.window().pm.profiles():
        return False
    if not util.window().isVisible():
        util.window().pm.load(name)
        util.window().loadProfile()
        util.window().profileDiag.closeWithoutQuitting()
    else:
        cur_profile = util.window().pm.name
        if cur_profile != name:
            util.window().unloadProfileAndShowProfileManager()
            loadProfile(name)
    return True


@util.api()
def multi(actions):
    return list(map(util.handler, actions))
