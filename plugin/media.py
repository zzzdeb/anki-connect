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

import base64
import os.path
import unicodedata

from . import util


@util.api()
def storeMediaFile(filename, data):
    util.deleteMediaFile(filename)
    util.media().writeData(filename, base64.b64decode(data))


@util.api()
def retrieveMediaFile(filename):
    filename = os.path.basename(filename)
    filename = unicodedata.normalize('NFC', filename)
    filename = util.media().stripIllegal(filename)

    path = os.path.join(util.media().dir(), filename)
    if os.path.exists(path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode('ascii')

    return False


@util.api()
def deleteMediaFile(filename):
    util.media().syncDelete(filename)
