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

import hashlib

import anki

from . import util


@util.api()
def addNote(note):
    ankiNote = createNote(note)

    audio = note.get('audio')
    if audio is not None and len(audio['fields']) > 0:
        try:
            data = util.download(audio['url'])
            skipHash = audio.get('skipHash')
            if skipHash is None:
                skip = False
            else:
                m = hashlib.md5()
                m.update(data)
                skip = skipHash == m.hexdigest()

            if not skip:
                audioFilename = util.media().writeData(audio['filename'], data)
                for field in audio['fields']:
                    if field in ankiNote:
                        ankiNote[field] += u'[sound:{}]'.format(audioFilename)

        except Exception as e:
            errorMessage = str(e).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            for field in audio['fields']:
                if field in ankiNote:
                    ankiNote[field] += errorMessage

    collection = util.collection()
    util.startEditing()
    nCardsAdded = collection.addNote(ankiNote)
    if nCardsAdded < 1:
        raise Exception('The field values you have provided would make an empty question on all cards.')
    collection.autosave()
    util.stopEditing()

    return ankiNote.id


@util.api()
def addNotes(notes):
    results = []
    for note in notes:
        try:
            results.append(addNote(note))
        except Exception:
            results.append(None)

    return results


@util.api()
def canAddNote(note):
    try:
        return bool(createNote(note))
    except:
        return False


@util.api()
def canAddNotes(notes):
    results = []
    for note in notes:
        results.append(canAddNote(note))

    return results


@util.api()
def updateNoteFields(note):
    ankiNote = util.collection().getNote(note['id'])
    if ankiNote is None:
        raise Exception('note was not found: {}'.format(note['id']))

    for name, value in note['fields'].items():
        if name in ankiNote:
            ankiNote[name] = value

    ankiNote.flush()


@util.api()
def addTags(notes, tags, add=True):
    util.startEditing()
    util.collection().tags.bulkAdd(notes, tags, add)
    util.stopEditing()


@util.api()
def removeTags(notes, tags):
    return addTags(notes, tags, False)


@util.api()
def getTags():
    return collection().tags.all()


@util.api()
def findNotes(query=None):
    if query is None:
        return []
    else:
        return util.collection().findNotes(query)


@util.api()
def notesInfo(notes):
    result = []
    for nid in notes:
        try:
            note = util.collection().getNote(nid)
            model = note.model()

            fields = {}
            for info in model['flds']:
                order = info['ord']
                name = info['name']
                fields[name] = {'value': note.fields[order], 'order': order}

            result.append({
                'noteId': note.id,
                'tags' : note.tags,
                'fields': fields,
                'modelName': model['name'],
                'cards': util.collection().db.list('select id from cards where nid = ? order by ord', note.id)
            })
        except TypeError as e:
            # Anki will give a TypeError if the note ID does not exist.
            # Best behavior is probably to add an 'empty card' to the
            # returned result, so that the items of the input and return
            # lists correspond.
            result.append({})

    return result


@util.api()
def deleteNotes(notes):
    try:
        util.collection().remNotes(notes)
    finally:
        util.stopEditing()


def createNote(note):
    collection = util.collection()

    model = collection.models.byName(note['modelName'])
    if model is None:
        raise Exception('model was not found: {}'.format(note['modelName']))

    deck = collection.decks.byName(note['deckName'])
    if deck is None:
        raise Exception('deck was not found: {}'.format(note['deckName']))

    ankiNote = anki.notes.Note(collection, model)
    ankiNote.model()['did'] = deck['id']
    ankiNote.tags = note['tags']

    for name, value in note['fields'].items():
        if name in ankiNote:
            ankiNote[name] = value

    allowDuplicate = False
    if 'options' in note:
        if 'allowDuplicate' in note['options']:
        allowDuplicate = note['options']['allowDuplicate']
        if type(allowDuplicate) is not bool:
            raise Exception('option parameter \'allowDuplicate\' must be boolean')

    duplicateOrEmpty = ankiNote.dupeOrEmpty()
    if duplicateOrEmpty == 1:
        raise Exception('cannot create note because it is empty')
    elif duplicateOrEmpty == 2:
        if not allowDuplicate:
        raise Exception('cannot create note because it is a duplicate')
        else:
        return ankiNote
    elif duplicateOrEmpty == False:
        return ankiNote
    else:
        raise Exception('cannot create note for unknown reason')
