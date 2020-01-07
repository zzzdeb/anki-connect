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

import anki
import aqt

from . import util


@util.api()
def deckNames():
    return util.decks().allNames()


@util.api()
def deckNamesAndIds():
    decks = {}
    for deck in deckNames():
        decks[deck] = util.decks().id(deck)

    return decks


@util.api()
def getDecks(cards):
    decks = {}
    for card in cards:
        did = util.database().scalar('select did from cards where id=?', card)
        deck = util.decks().get(did)['name']
        if deck in decks:
            decks[deck].append(card)
        else:
            decks[deck] = [card]

    return decks


@util.api()
def createDeck(deck):
    try:
        util.startEditing()
        did = util.decks().id(deck)
    finally:
        util.stopEditing()

    return did


@util.api()
def changeDeck(cards, deck):
    util.startEditing()

    did = util.collection().decks.id(deck)
    mod = anki.utils.intTime()
    usn = util.collection().usn()

    # normal cards
    scids = anki.utils.ids2str(cards)
    # remove any cards from filtered deck first
    util.collection().sched.remFromDyn(cards)

    # then move into new deck
    util.collection().db.execute('update cards set usn=?, mod=?, did=? where id in ' + scids, usn, mod, did)
    util.stopEditing()


@util.api()
def deleteDecks(decks, cardsToo=False):
    try:
        util.startEditing()
        decks = filter(lambda d: d in deckNames(), decks)
        for deck in decks:
            did = util.decks().id(deck)
            util.decks().rem(did, cardsToo)
    finally:
        util.stopEditing()


@util.api()
def getDeckConfig(deck):
    if not deck in deckNames():
        return False

    collection = util.collection()
    did = collection.decks.id(deck)
    return collection.decks.confForDid(did)


@util.api()
def saveDeckConfig(config):
    collection = util.collection()

    config['id'] = str(config['id'])
    config['mod'] = anki.utils.intTime()
    config['usn'] = collection.usn()

    if not config['id'] in collection.decks.dconf:
        return False

    collection.decks.dconf[config['id']] = config
    collection.decks.changed = True
    return True


@util.api()
def setDeckConfigId(decks, configId):
    configId = str(configId)
    for deck in decks:
        if not deck in deckNames():
            return False

    collection = util.collection()
    if not configId in collection.decks.dconf:
        return False

    for deck in decks:
        did = str(collection.decks.id(deck))
        aqt.mw.col.decks.decks[did]['conf'] = configId

    return True


@util.api()
def cloneDeckConfigId(name, cloneFrom='1'):
    configId = str(cloneFrom)
    if not configId in util.collection().decks.dconf:
        return False

    config = util.collection().decks.getConf(configId)
    return util.collection().decks.confId(name, config)


@util.api()
def removeDeckConfigId(configId):
    configId = str(configId)
    collection = util.collection()
    if configId == 1 or not configId in collection.decks.dconf:
        return False

    collection.decks.remConf(configId)
    return True
