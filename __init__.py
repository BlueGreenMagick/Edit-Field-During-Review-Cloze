# -*- coding: utf-8 -*-


import base64
import unicodedata
import json
from pathlib import Path

from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from anki import version as ankiversion

from aqt import mw
from aqt.qt import QClipboard
from aqt.editor import Editor
from aqt.reviewer import Reviewer
from aqt.utils import tooltip, showText

from .semieditor import semiEditorWebView


config = mw.addonManager.getConfig(__name__)

ankiver_minor = int(ankiversion.split('.')[2])
ankiver_major = ankiversion[0:3]

#Get js files.
def js_from_path(path):
    return "<script>" + path.read_text() + "</script>"

DIRPATH = Path(__file__).parents[0]

CARDJS = js_from_path(DIRPATH / "card.js")
GLOBALCARDJS = js_from_path(DIRPATH / "global_card.js")
PASTEJS = js_from_path(DIRPATH / "paste.js")
BOTTOMJS = js_from_path(DIRPATH / "bottom.js")


if config["process_paste"]:
    editorwv = semiEditorWebView()

def bool_to_str(b):
    if b:
        return "true"
    else:
        return ""

#Code for new style hooks.
def new_fld_hook(txt, field, filt, ctx):
    if filt == "edit":
        return edit(txt, None, None, field, None)
#from anki import hooks 
#hooks.field_filter.append(new_fld_hook)

def myRevHtml(reviewer, _old):
    span = bool_to_str(config["tag"])
    ctrl = bool_to_str(config["ctrl_click"])
    paste = bool_to_str(config["process_paste"])
    rem_span = bool_to_str(config["remove_span"])
    special = json.dumps(config["special_formatting"])

    js = GLOBALCARDJS%({"span":span, "ctrl":ctrl, "paste": paste, "remove_span": rem_span, "special": special})

    if config["process_paste"]:
        js += PASTEJS

    return _old(reviewer) + js

def myRevBottomHTML(reviewer, _old):
    ctrl = bool_to_str(config["ctrl_click"])
    script = BOTTOMJS%({"ctrl":ctrl})

    return _old(reviewer) + script

def edit(txt, extra, context, field, fullname):
    ctrl = bool_to_str(config["ctrl_click"])
    
    #Encode field to escape special characters.
    field = base64.b64encode(field.encode('utf-8')).decode('ascii')
    txt = """<%s data-EFDRCfield="%s" data-EFDRC="true">%s</%s>""" % (
        config['tag'], field, txt, config['tag'])
    txt += CARDJS % ({"fld":field})

    mw.reviewer.bottom.web.eval(BOTTOMJS% ({"ctrl":ctrl}))
    return txt


def saveField(note, fld, val):
    if fld == "Tags":
        tagsTxt = unicodedata.normalize("NFC", htmlToTextLine(val))
        txt = mw.col.tags.canonify(mw.col.tags.split(tagsTxt))
        field = note.tags
    else:
        #aqt.editor.Editor.onBridgeCmd
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
    if url.startswith("EFDRC#"):
        ERROR_MSG = "ERROR - Edit Field During Review Cloze\nSomething unexpected occured. The edit may not have been saved. %s"
        enc_val, fld, new_val = url.replace("EFDRC#", "").split("#", 2)
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

    #Reset timer from Speed Focus Mode add-on.
    elif url.startswith("EFDRC!speedfocus#"):
        reviewer.bottom.web.eval("""
            clearTimeout(autoAnswerTimeout);
            clearTimeout(autoAlertTimeout);
            clearTimeout(autoAgainTimeout);
        """)
    
    #Replace reviewer field html if it is different from real field value.
    #For example, clozes, mathjax, audio.
    elif url.startswith("EFDRC!focuson#"):
        fld = url.replace("EFDRC!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode('utf-8')
        val = reviewer.card.note()[decoded_fld]
        encoded_val = base64.b64encode(val.encode('utf-8')).decode('ascii')
        reviewer.web.eval("""
        var encoded_val = "%s";
        var val = EFDRC.b64DecodeUnicode(encoded_val);
        var elems = document.querySelectorAll("[data-EFDRCfield='%s']")
        for(var e = 0; e < elems.length; e++){
            var elem = elems[e];
            elem.setAttribute("data-EFDRCval", encoded_val);
            if(elem.innerHTML != val){
                elem.innerHTML = val;
            }
        }
        """ % (encoded_val, fld))
    elif url == "EFDRC!reload":
        if reviewer.state == "question":
            reviewer._showQuestion()
        elif reviewer.state == "answer":
            reviewer._showAnswer()
    
    #Catch ctrl key presses from bottom.web.
    elif url == "EFDRC!ctrldown":
        reviewer.web.eval("EFDRC.ctrldown()")
    elif url == "EFDRC!ctrlup":
        reviewer.web.eval("EFDRC.ctrlup()")

    elif url == "EFDRC!paste":
        #From aqt.editor.Editor._onPaste, doPaste.
        mime = mw.app.clipboard().mimeData(mode=QClipboard.Clipboard)
        html, internal = editorwv._processMime(mime)
        html = editorwv.editor._pastePreFilter(html, internal)
        reviewer.web.eval("pasteHTML(%s, %s);"% (json.dumps(html), json.dumps(internal)))
    
    elif url.startswith("EFDRC!debug#"):
        fld = url.replace("EFDRC!debug#", "")
        showText(fld)
    else:
        return _old(reviewer, url)

Reviewer._bottomHTML = wrap(Reviewer._bottomHTML, myRevBottomHTML, "around")
Reviewer.revHtml = wrap(Reviewer.revHtml, myRevHtml, "around")
Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
addHook('fmod_edit', edit)