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

import time

import anki

from . import util


@util.api()
def suspend(cards, suspend=True):
    for card in cards:
        if suspended(card) == suspend:
            cards.remove(card)

    if len(cards) == 0:
        return False

    scheduler = util.scheduler()
    util.startEditing()
    if suspend:
        scheduler.suspendCards(cards)
    else:
        scheduler.unsuspendCards(cards)
    util.stopEditing()

    return True


@util.api()
def unsuspend(cards):
    suspend(cards, False)


@util.api()
def suspended(card):
    card = util.collection().getCard(card)
    return card.queue == -1


@util.api()
def areSuspended(cards):
    suspended = []
    for card in cards:
        suspended.append(suspended(card))

    return suspended


@util.api()
def areDue(cards):
    due = []
    for card in cards:
        if findCards('cid:{} is:new'.format(card)):
            due.append(True)
        else:
            date, ivl = util.collection().db.all('select id/1000.0, ivl from revlog where cid = ?', card)[-1]
            if ivl >= -1200:
                due.append(bool(findCards('cid:{} is:due'.format(card))))
            else:
                due.append(date - ivl <= time.time())

    return due


@util.api()
def getIntervals(cards, complete=False):
    intervals = []
    for card in cards:
        if findCards('cid:{} is:new'.format(card)):
            intervals.append(0)
        else:
            interval = util.collection().db.list('select ivl from revlog where cid = ?', card)
            if not complete:
                interval = interval[-1]
            intervals.append(interval)

    return intervals


@util.api()
def findCards(query=None):
    if query is None:
        return []
    else:
        return util.collection().findCards(query)


@util.api()
def cardsToNotes(cards):
    return util.collection().db.list('select distinct nid from cards where id in ' + anki.utils.ids2str(cards))


@util.api()
def cardsInfo(cards):
    result = []
    for cid in cards:
        try:
            card = util.collection().getCard(cid)
            model = card.model()
            note = card.note()
            fields = {}
            for info in model['flds']:
                order = info['ord']
                name = info['name']
                fields[name] = {'value': note.fields[order], 'order': order}

            result.append({
                'cardId': card.id,
                'fields': fields,
                'fieldOrder': card.ord,
                'question': card._getQA()['q'],
                'answer': card._getQA()['a'],
                'modelName': model['name'],
                'deckName': util.deckNameFromId(card.did),
                'css': model['css'],
                'factor': card.factor,
                #This factor is 10 times the ease percentage,
                # so an ease of 310% would be reported as 3100
                'interval': card.ivl,
                'note': card.nid
            })
        except TypeError as e:
            # Anki will give a TypeError if the card ID does not exist.
            # Best behavior is probably to add an 'empty card' to the
            # returned result, so that the items of the input and return
            # lists correspond.
            result.append({})

    return result
