# -*- coding: utf-8 -*-

"""
Anki Add-on: Import from Airtable

Import data from Airtable

Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
"""

import csv
import io
import os
import requests
import time

from aqt import mw, editcurrent, addcards, editor
from aqt.utils import getFile, tooltip
from anki.lang import _, ngettext
from anki.models import defaultModel
from anki.hooks import wrap
from aqt.qt import *

from .importing import Ui_Dialog

config = mw.addonManager.getConfig(__name__)

class AirtableImporter:

    def __init__(self):
        self.init()

    def init(self):
        d = QDialog(mw)
        d.setWindowModality(Qt.WindowModal)
        frm = Ui_Dialog()
        frm.setupUi(d)

        def selectFile():
            file = getFile(mw, _("Select File"), None, (_("Airtable CSV Export (*.csv)")), key="import")
            if not file:
                return
            file = str(file)
            frm.csvPath.setText(file)

        frm.openBtn.clicked.connect(selectFile)
        if config['api_key']:
            frm.apiKey.setText(config['api_key'])

        def updateTableAndView(text):
            table, view = os.path.splitext(os.path.basename(text))[0].rsplit("-", 1)
            frm.tableName.setText(table)
            frm.viewName.setText(view)

        frm.csvPath.textChanged.connect(updateTableAndView)

        if not d.exec_():
            return

        self.total = 0
        self.apiKey = frm.apiKey.text().strip()
        self.baseKey = frm.baseKey.text().strip()
        self.csvPath = frm.csvPath.text().strip()
        self.tableName = frm.tableName.text().strip()
        self.viewName = frm.viewName.text().strip()
        
        mw.checkpoint("Import from Airtable")
        mw.progress.start(immediate=True)

        fieldnames = self.getFieldNames(self.csvPath)
        model = self.addNewNoteType(fieldnames)
        mw.col.models.setCurrent(model)
        self.modelName = model['name']

        config['api_key'] = self.apiKey
        config['models'][self.modelName] = {}
        config['models'][self.modelName]["base_key"] = self.baseKey
        config['models'][self.modelName]["table_name"] = self.tableName
        config['models'][self.modelName]["view_name"] = self.viewName
        mw.addonManager.writeConfig(__name__, config)

        did = mw.col.decks.id(self.tableName)
        thread = Downloader(self.apiKey, self.baseKey, self.tableName, self.viewName)

        def onRecv(records):
            for r in records:
                fields = r["fields"]
                note = mw.col.newNote(forDeck=False)
                note['id'] = r['id']
                for f in fields:
                    if f in note:
                        note[f] = fields[f]
                note.model()['did'] = did
                mw.col.addNote(note)
                self.total += 1
                mw.progress.update(label=ngettext("%d note imported.", "%d notes imported.", self.total) % self.total)

        thread.recv.connect(onRecv)
        thread.start()
        while not thread.isFinished():
            mw.app.processEvents()
            thread.wait(100)

        mw.progress.finish()
        mw.reset()
        tooltip(ngettext("%d note imported.", "%d notes imported.", self.total) % self.total, period=1000)

    def getFieldNames(self, csvPath):
        with io.open(csvPath, "r", encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return reader.fieldnames

    def addNewNoteType(self, fields):
        model = mw.col.models.new(self.tableName)
        model['css'] = defaultModel['css']
        mw.col.models.addField(model, mw.col.models.newField("id"))
        for fld in fields:
            mw.col.models.addField(model, mw.col.models.newField(fld))
        t = mw.col.models.newTemplate("Card 1")
        t['qfmt'] = "{{" + fields[0] + "}}"
        t['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n" + "{{" + fields[:2][-1] + "}}"
        mw.col.models.addTemplate(model, t)
        mw.col.models.add(model)
        return model

class Downloader(QThread):
    
    recv = pyqtSignal('PyQt_PyObject')

    def __init__(self, apiKey, baseKey, tableName, viewName):
        QThread.__init__(self)
        self.apiKey = apiKey
        self.baseKey = baseKey
        self.tableName = tableName
        self.viewName = viewName
        self.headers = { "Authorization": "Bearer {}".format(self.apiKey) }

    def run(self):
        offset = self.getRecords(self.headers)
        while offset is not None:
            time.sleep(0.2) # prevent 429 status code and 30 seconds wait before subsequent requests will succeed
            offset = self.getRecords(self.headers, offset=offset)

    def getRecords(self, headers, offset=None):
        payload = {}
        payload['view'] = self.viewName
        if offset is not None:
            payload['offset'] = offset
        r = requests.get( "https://api.airtable.com/v0/{}/{}".format(self.baseKey, self.tableName), headers=headers, params=payload )
        r.raise_for_status()
        if r.status_code == 200:
            data = r.json()
            records = data["records"]
            if "offset" in data:
                offset = data["offset"]
            else:
                offset = None
            self.recv.emit(records)
            return offset

def prepareData(note):
    data = {}
    data["fields"] = {}
    fields = note.keys()
    for fld in fields:
        if fld != "id":
            data["fields"][fld] = note[fld]
    data["typecast"] = True
    return data

def updateRecord(self):
    note = self.mw.reviewer.card.note()
    model = note.model()['name']
    if model not in config['models']:
        return
    data = prepareData(note)
    headers = { "Authorization": "Bearer {}".format(config['api_key']) }
    conf = config['models'][model]
    r = requests.patch("https://api.airtable.com/v0/{}/{}/{}".format(conf["base_key"], conf["table_name"], note["id"]), headers=headers, json=data )
    r.raise_for_status()

def mySaveAndClose(self, _old):
    updateRecord(self)
    ret = _old(self)
    return ret

editcurrent.EditCurrent._saveAndClose = wrap(editcurrent.EditCurrent._saveAndClose, mySaveAndClose, "around")

def addRecord(self, note):
    data = prepareData(note)
    model = note.model()['name']
    headers = { "Authorization": "Bearer {}".format(config['api_key']) }
    conf = config['models'][model]
    r = requests.post("https://api.airtable.com/v0/{}/{}".format(conf["base_key"], conf["table_name"]), headers=headers, json=data )
    r.raise_for_status()
    data = r.json()
    note["id"] = data["id"]
    note.flush()

def myAddNote(self, note, _old):
    model = note.model()['name']
    if model not in config['models']:
        return _old(self, note)
    note["id"] = "###"
    ret = _old(self, note)
    if not ret:
        return
    addRecord(self, note)
    return note

addcards.AddCards.addNote = wrap(addcards.AddCards.addNote, myAddNote, "around")

def setupWeb(self):
    self.web.eval("""
        var style = $('<style>.airtable-id tr:nth-child(-n+2) { display: none; }</style>');
        $('html > head').append(style);
    """)

def loadNote(self, focusTo=None):
    model = self.note.model()['name']
    if model in config['models']:
        self.web.eval("$('#fields').addClass('airtable-id');")
    else:
        self.web.eval("$('#fields').removeClass('airtable-id').filter('[class=""]').removeAttr('class');")

editor.Editor.setupWeb = wrap(editor.Editor.setupWeb, setupWeb, "after")
editor.Editor.loadNote = wrap(editor.Editor.loadNote, loadNote, "before")

def onImport():
    AirtableImporter()

action = QAction("Import from Airtable", mw)
action.triggered.connect(onImport)
mw.form.menuTools.addAction(action)
