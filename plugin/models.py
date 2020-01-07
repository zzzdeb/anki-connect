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
import hashlib
import inspect
import json
import os
import os.path
import random
import re
import string
import time
import unicodedata

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

import anki
import anki.lang
import aqt

from . import web, util


@util.api()
def modelNames():
    return util.collection().models.allNames()


@util.api()
def modelNamesAndIds():
    models = {}
    for model in modelNames():
        models[model] = int(util.collection().models.byName(model)['id'])

    return models


@util.api()
def modelFieldNames(modelName):
    model = util.collection().models.byName(modelName)
    if model is None:
        raise Exception('model was not found: {}'.format(modelName))
    else:
        return [field['name'] for field in model['flds']]


@util.api()
def modelFieldsOnTemplates(modelName):
    model = util.collection().models.byName(modelName)
    if model is None:
        raise Exception('model was not found: {}'.format(modelName))

    templates = {}
    for template in model['tmpls']:
        fields = []
        for side in ['qfmt', 'afmt']:
            fieldsForSide = []

            # based on _fieldsOnTemplate from aqt/clayout.py
            matches = re.findall('{{[^#/}]+?}}', template[side])
            for match in matches:
                # remove braces and modifiers
                match = re.sub(r'[{}]', '', match)
                match = match.split(':')[-1]

                # for the answer side, ignore fields present on the question side + the FrontSide field
                if match == 'FrontSide' or side == 'afmt' and match in fields[0]:
                    continue
                fieldsForSide.append(match)

            fields.append(fieldsForSide)

        templates[template['name']] = fields

    return templates


@util.api()
def createModel(modelName, inOrderFields, cardTemplates, css = None):
    # https://github.com/dae/anki/blob/b06b70f7214fb1f2ce33ba06d2b095384b81f874/anki/stdmodels.py
    if (len(inOrderFields) == 0):
        raise Exception('Must provide at least one field for inOrderFields')
    if (len(cardTemplates) == 0):
        raise Exception('Must provide at least one card for cardTemplates')
    if (modelName in util.collection().models.allNames()):
        raise Exception('Model name already exists')

    collection = util.collection()
    mm = collection.models

    # Generate new Note
    m = mm.new(anki.lang._(modelName))

    # Create fields and add them to Note
    for field in inOrderFields:
        fm = mm.newField(anki.lang._(field))
        mm.addField(m, fm)

    # Add shared css to model if exists. Use default otherwise
    if (css is not None):
        m['css'] = css

    # Generate new card template(s)
    cardCount = 1
    for card in cardTemplates:
        t = mm.newTemplate(anki.lang._('Card ' + str(cardCount)))
        cardCount += 1
        t['qfmt'] = card['Front']
        t['afmt'] = card['Back']
        mm.addTemplate(m, t)

    mm.add(m)
    return m


@util.api()
def modelTemplates(modelName):
    model = util.collection().models.byName(modelName)
    if model is None:
        raise Exception('model was not found: {}'.format(modelName))

    templates = {}
    for template in model['tmpls']:
        templates[template['name']] = {'Front': template['qfmt'], 'Back': template['afmt']}

    return templates


@util.api()
def modelStyling(modelName):
    model = util.collection().models.byName(modelName)
    if model is None:
        raise Exception('model was not found: {}'.format(modelName))

    return {'css': model['css']}


@util.api()
def updateModelTemplates(model):
    models = util.collection().models
    ankiModel = models.byName(model['name'])
    if ankiModel is None:
        raise Exception('model was not found: {}'.format(model['name']))

    templates = model['templates']

    for ankiTemplate in ankiModel['tmpls']:
        template = templates.get(ankiTemplate['name'])
        if template:
            qfmt = template.get('Front')
            if qfmt:
                ankiTemplate['qfmt'] = qfmt

            afmt = template.get('Back')
            if afmt:
                ankiTemplate['afmt'] = afmt

    models.save(ankiModel, True)
    models.flush()


@util.api()
def updateModelStyling(model):
    models = util.collection().models
    ankiModel = models.byName(model['name'])
    if ankiModel is None:
        raise Exception('model was not found: {}'.format(model['name']))

    ankiModel['css'] = model['css']

    models.save(ankiModel, True)
    models.flush()


@util.api()
def modelNameFromId(modelId):
    model = util.collection().models.get(modelId)
    if model is None:
        raise Exception('model was not found: {}'.format(modelId))
    else:
        return model['name']
