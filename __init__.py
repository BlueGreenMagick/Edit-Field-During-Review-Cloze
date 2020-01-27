# -*- coding: utf-8 -*-

"""
Anki Add-on: Edit Field During Review Cloze
Edit text in a field during review without opening the edit window
Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
Modified by <bluegreenmagick@gmail.com>
"""

import base64
import unicodedata
import urllib.parse
import json

from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from anki import version as ankiversion

from aqt import mw
from aqt.qt import QClipboard
from aqt.editor import Editor
from aqt.reviewer import Reviewer
from aqt.utils import tooltip, showInfo
from aqt.editor import Editor

from .semieditor import semiEditorWebView
from .web import bottom_js, paste_js, card_js


config = mw.addonManager.getConfig(__name__)
ankiver_minor = int(ankiversion.split('.')[2])
ankiver_major = ankiversion[0:3]

if config["process_paste"]:
    editorwv = semiEditorWebView()


def bool_to_str(b):
    if b:
        return "true"
    else:
        return "false"

#code for new style hooks
#from anki import hooks 
#hooks.field_filter.append(new_fld_hook)
def new_fld_hook(txt, field, filt, ctx):
    if filt == "edit":
        return edit(txt, None, None, field, None)

def edit(txt, extra, context, field, fullname):
    span = bool_to_str(config["tag"])
    ctrl = bool_to_str(config["ctrl_click"])
    paste = bool_to_str(config["process_paste"])

    field = base64.b64encode(field.encode('utf-8')).decode('ascii')
    txt = """<%s data-EFDRCfield="%s" data-EFDRC="true">%s</%s>""" % (
        config['tag'], field, txt, config['tag'])
    txt += card_js % ({"fld":field, "span":span, "ctrl":ctrl, "paste": paste})
    if config["process_paste"]:
        txt += paste_js
    mw.reviewer.bottom.web.eval(bottom_js% ({"ctrl":ctrl}))
    return txt


def saveField(note, fld, val):
    if fld == "Tags":
        tagsTxt = unicodedata.normalize("NFC", htmlToTextLine(val))
        txt = mw.col.tags.canonify(mw.col.tags.split(tagsTxt))
        field = note.tags
    else:
        # https://github.com/dae/anki/blob/47eab46f05c8cc169393c785f4c3f49cf1d7cca8/aqt/editor.py#L257-L263
        txt = urllib.parse.unquote(val)
        txt = unicodedata.normalize("NFC", txt)
        txt = Editor.mungeHTML(None, txt)
        txt = txt.replace("\x00", "")
        txt = mw.col.media.escapeImages(txt, unescape=True)
        field = note[fld]
    if field == txt:
        return
    config = mw.addonManager.getConfig(__name__)
    if config['undo']:
        mw.checkpoint("Edit Field")
    if fld == "Tags":
        note.tags = txt
    else:
        note[fld] = txt
    note.flush()

def saveThenRefreshFld(reviewer, note, fld, new_val):
    saveField(note, fld, new_val)
    if ankiver_major == "2.1" and ankiver_minor < 20:
        reviewer.card._getQA(reload=True)
    else:
        reviewer.card.render_output(reload=True)

def myLinkHandler(reviewer, url, _old):
    if url.startswith("ankisave#"):
        ERROR_MSG = "ERROR - Edit Field During Review Cloze\nSomething unexpected occured. The edit may not have been saved. %s"
        enc_val, fld, new_val = url.replace("ankisave#", "").split("#", 2)
        note = reviewer.card.note()
        fld = base64.b64decode(fld, validate=True).decode('utf-8')
        if fld not in note:
            tooltip(ERROR_MSG%fld)
        orig_val = note[fld]
        orig_enc_val = base64.b64encode(orig_val.encode('utf-8')).decode('ascii')
        if enc_val == orig_enc_val: #enc_val may be the val of prev reviewed card.
            saveThenRefreshFld(reviewer, note, fld, new_val)
        else:
            tooltip(ERROR_MSG%fld)

    elif url.startswith("ankisave!speedfocus#"):
        reviewer.bottom.web.eval("""
            clearTimeout(autoAnswerTimeout);
            clearTimeout(autoAlertTimeout);
            clearTimeout(autoAgainTimeout);
        """)
    elif url.startswith("ankisave!focuson#"):
        fld = url.replace("ankisave!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode('utf-8')
        val = reviewer.card.note()[decoded_fld]
        encoded_val = base64.b64encode(val.encode('utf-8')).decode('ascii')
        reviewer.web.eval("""
        var encoded_val = "%s";
        var val = b64DecodeUnicode(encoded_val);
        var elems = document.querySelectorAll("[data-EFDRCfield='%s']")
        for(var e = 0; e < elems.length; e++){
            var elem = elems[e];
            elem.setAttribute("data-EFDRCval", encoded_val);
            if(elem.innerHTML != val){
                elem.innerHTML = val;
            }
        }
        """ % (encoded_val, fld))
    elif url == "ankisave!reload":
        if reviewer.state == "question":
            reviewer._showQuestion()
        elif reviewer.state == "answer":
            reviewer._showAnswer()
    elif url == "EFDRC#ctrldown":
        reviewer.web.eval("EFDRCctrldown()")
    elif url == "EFDRC#ctrlup":
        reviewer.web.eval("EFDRCctrlup()")
    elif url == "EFDRC#paste":
        #use processMime function a little modified in anki source!
        mime = mw.app.clipboard().mimeData(mode=QClipboard.Clipboard)
        html, internal = editorwv._processMime(mime)
        html = editorwv.editor._pastePreFilter(html, internal)
        reviewer.web.eval("pasteHTML(%s, %s);"% (json.dumps(html), json.dumps(internal)))
    elif url.startswith("EFDRC#debug#"):
        fld = url.replace("EFDRC#debug#", "")
        showInfo(fld)
    else:
        return _old(reviewer, url)


Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
addHook('fmod_edit', edit)