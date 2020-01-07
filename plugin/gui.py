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

import random
import string

from PyQt5.QtCore import QTimer

import aqt

from . import util


@util.api()
def guiBrowse(query=None):
    browser = aqt.dialogs.open('Browser', util.window())
    browser.activateWindow()

    if query is not None:
        browser.form.searchEdit.lineEdit().setText(query)
        if hasattr(browser, 'onSearch'):
            browser.onSearch()
        else:
            browser.onSearchActivated()

    return browser.model.cards


@util.api()
def guiAddCards(note=None):

    if note is not None:
        collection = util.collection()

        deck = collection.decks.byName(note['deckName'])
        if deck is None:
            raise Exception('deck was not found: {}'.format(note['deckName']))

        util.collection().decks.select(deck['id'])
        savedMid = deck.pop('mid', None)

        model = collection.models.byName(note['modelName'])
        if model is None:
            raise Exception('model was not found: {}'.format(note['modelName']))

        util.collection().models.setCurrent(model)
        util.collection().models.update(model)

    closeAfterAdding = False
    if note is not None and 'options' in note:
        if 'closeAfterAdding' in note['options']:
            closeAfterAdding = note['options']['closeAfterAdding']
            if type(closeAfterAdding) is not bool:
                raise Exception('option parameter \'closeAfterAdding\' must be boolean')

    addCards = None

    if closeAfterAdding:
        randomString = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        windowName = 'AddCardsAndClose' + randomString

        class AddCardsAndClose(aqt.addcards.AddCards):

            def __init__(self, mw):
                # the window must only reset if
                # * function `onModelChange` has been called prior
                # * window was newly opened

                util.modelHasChanged = True
                super().__init__(mw)

                util.addButton.setText("Add and Close")
                util.addButton.setShortcut(aqt.qt.QKeySequence("Ctrl+Return"))

            def _addCards(self):
                super()._addCards()

                # if adding was successful it must mean it was added to the history of the window
                if len(util.history):
                    util.reject()

            def onModelChange(self):
                if util.isActiveWindow():
                    super().onModelChange()
                    util.modelHasChanged = True

            def onReset(self, model=None, keep=False):
                if util.isActiveWindow() or util.modelHasChanged:
                    super().onReset(model, keep)
                    util.modelHasChanged = False

                else:
                    # modelchoosers text is changed by a reset hook
                    # therefore we need to change it back manually
                    util.modelChooser.models.setText(util.editor.note.model()['name'])
                    util.modelHasChanged = False

            def _reject(self):
                savedMarkClosed = aqt.dialogs.markClosed
                aqt.dialogs.markClosed = lambda _: savedMarkClosed(windowName)
                super()._reject()
                aqt.dialogs.markClosed = savedMarkClosed

        aqt.dialogs._dialogs[windowName] = [AddCardsAndClose, None]
        addCards = aqt.dialogs.open(windowName, util.window())

        if savedMid:
            deck['mid'] = savedMid

        editor = addCards.editor
        ankiNote = editor.note

        if 'fields' in note:
            for name, value in note['fields'].items():
                if name in ankiNote:
                    ankiNote[name] = value
            editor.loadNote()

        if 'tags' in note:
            ankiNote.tags = note['tags']
            editor.updateTags()

        # if Anki does not Focus, the window will not notice that the
        # fields are actually filled
        aqt.dialogs.open(windowName, util.window())
        addCards.setAndFocusNote(editor.note)

    elif note is not None:
        currentWindow = aqt.dialogs._dialogs['AddCards'][1]

        def openNewWindow():
            addCards = aqt.dialogs.open('AddCards', util.window())

            if savedMid:
                deck['mid'] = savedMid

            editor = addCards.editor
            ankiNote = editor.note

            # we have to fill out the card in the callback
            # otherwise we can't assure, the new window is open
            if 'fields' in note:
                for name, value in note['fields'].items():
                    if name in ankiNote:
                        ankiNote[name] = value
                editor.loadNote()

            if 'tags' in note:
                ankiNote.tags = note['tags']
                editor.updateTags()

            addCards.activateWindow()

            aqt.dialogs.open('AddCards', util.window())
            addCards.setAndFocusNote(editor.note)

        if currentWindow is not None:
            currentWindow.closeWithCallback(openNewWindow)
        else:
            openNewWindow()

    else:
        addCards = aqt.dialogs.open('AddCards', util.window())
        addCards.activateWindow()

@util.api()
def guiReviewActive():
    return util.reviewer().card is not None and util.window().state == 'review'


@util.api()
def guiCurrentCard():
    if not util.guiReviewActive():
        raise Exception('Gui review is not currently active.')

    reviewer = util.reviewer()
    card = reviewer.card
    model = card.model()
    note = card.note()

    fields = {}
    for info in model['flds']:
        order = info['ord']
        name = info['name']
        fields[name] = {'value': note.fields[order], 'order': order}

    if card is not None:
        buttonList = reviewer._answerButtonList()
        return {
            'cardId': card.id,
            'fields': fields,
            'fieldOrder': card.ord,
            'question': card._getQA()['q'],
            'answer': card._getQA()['a'],
            'buttons': [b[0] for b in buttonList],
            'nextReviews': [reviewer.mw.col.sched.nextIvlStr(reviewer.card, b[0], True) for b in buttonList],
            'modelName': model['name'],
            'deckName': util.deckNameFromId(card.did),
            'css': model['css'],
            'template': card.template()['name']
        }


@util.api()
def guiStartCardTimer():
    if not util.guiReviewActive():
        return False

    card = util.reviewer().card

    if card is not None:
        card.startTimer()
        return True
    else:
        return False


@util.api()
def guiShowQuestion():
    if util.guiReviewActive():
        util.reviewer()._showQuestion()
        return True
    else:
        return False


@util.api()
def guiShowAnswer():
    if util.guiReviewActive():
        util.window().reviewer._showAnswer()
        return True
    else:
        return False


@util.api()
def guiAnswerCard(ease):
    if not util.guiReviewActive():
        return False

    reviewer = util.reviewer()
    if reviewer.state != 'answer':
        return False
    if ease <= 0 or ease > util.scheduler().answerButtons(reviewer.card):
        return False

    reviewer._answerCard(ease)
    return True


@util.api()
def guiDeckOverview(name):
    collection = util.collection()
    if collection is not None:
        deck = collection.decks.byName(name)
        if deck is not None:
            collection.decks.select(deck['id'])
            util.window().onOverview()
            return True

    return False


@util.api()
def guiDeckBrowser():
    util.window().moveToState('deckBrowser')


@util.api()
def guiDeckReview(name):
    if util.guiDeckOverview(name):
        util.window().moveToState('review')
        return True
    else:
        return False


@util.api()
def guiExitAnki():
    timer = QTimer()
    timer.timeout.connect(util.window().close)
    timer.start(1000) # 1s should be enough to allow the response to be sent.
