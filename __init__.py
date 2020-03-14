# -*- coding: utf-8 -*-


import base64
import json
import unicodedata
from pathlib import Path

from anki import version as ankiversion
from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from aqt import mw
from aqt.editor import Editor
from aqt.qt import QClipboard
from aqt.reviewer import Reviewer
from aqt.utils import showText, tooltip

from .semieditor import semiEditorWebView

config = mw.addonManager.getConfig(__name__)

ankiver_minor = int(ankiversion.split('.')[2])
ankiver_major = ankiversion[0:3]


# Get js files.
def js_from_path(path):
    return "<script>" + path.read_text() + "</script>"
def css_from_path(path):
    return "<style>" + path.read_text() + "</style>"


DIRPATH = Path(__file__).parents[0]

CARDJS = js_from_path(DIRPATH / "card.js")
GLOBALCARDJS = js_from_path(DIRPATH / "global_card.js")
RESIZEJS = js_from_path(DIRPATH / "resize.js")
JQUERYUIJS = js_from_path(DIRPATH / "jquery-ui.js")
JQUERYUICSS = css_from_path(DIRPATH / "jquery-ui.css")
PASTEJS = js_from_path(DIRPATH / "paste.js")
BOTTOMJS = js_from_path(DIRPATH / "bottom.js")

editorwv = semiEditorWebView()


def config_make_valid():
    global config

    sfmt = config["z_special_formatting"]
    default_sfmt = {
        "removeformat": True,
        "strikethrough": True,
        "fontcolor": [True, "#00f"],
        "highlight": [False, "#00f"],
        "subscript": False,
        "superscript": False,
        "formatblock": [False, "pre"],
        "hyperlink": False,
        "unhyperlink": False,
        "unorderedlist": False,
        "orderedlist": False,
        "indent": False,
        "outdent": False,
        "justifyCenter": False,
        "justifyLeft": False,
        "justifyRight": False,
        "justifyFull": False
    }

    changed = False

    # Remove wrong key.
    key_to_pop = []
    for key in sfmt:
        if key not in default_sfmt:
            key_to_pop.append(key)
            changed = True

    for key in key_to_pop:
        sfmt.pop(key)

    # Add keys on update / wrong deletion. 
    for key in default_sfmt:
        if key not in sfmt:
            sfmt[key] = default_sfmt[key]
            changed = True

    if changed:
        mw.addonManager.writeConfig(__name__, config)
        config = mw.addonManager.getConfig(__name__)


def bool_to_str(b):
    if b:
        return "true"
    else:
        return ""


# Code for new style hooks.
def new_fld_hook(txt, field, filt, ctx):
    if filt == "edit":
        return edit(txt, None, None, field, None)
#from anki import hooks
# hooks.field_filter.append(new_fld_hook)


def myRevHtml(reviewer, _old):
    global config
    config = mw.addonManager.getConfig(__name__)
    config_make_valid()

    span = bool_to_str(config["tag"])
    ctrl = bool_to_str(config["ctrl_click"])
    paste = bool_to_str(config["process_paste"])
    rem_span = bool_to_str(config["remove_span"])
    special = json.dumps(config["z_special_formatting"])
    preserve_ratio = bool_to_str(config["preserve_ratio"])
    min_height = config["min-height"]
    min_width = config["min-width"]
    style = JQUERYUICSS
    resizable_style = config["resizable-style"]
    if resizable_style:
        style += f"<style>.ui-wrapper {{   {resizable_style} }}</style>"

    js = JQUERYUIJS
    js += GLOBALCARDJS % ({"span": span, "ctrl": ctrl, "paste": paste,
                          "remove_span": rem_span, "special": special})
    js += RESIZEJS % ({"min_height": min_height, "min_width": min_width, "preserve_ratio": preserve_ratio, "resizable_style": resizable_style});

    if config["process_paste"]:
        js += PASTEJS

    if config["outline"]:
        style += "<style>[data-efdrc='true'][contenteditable='true']:focus{outline: 1px solid #308cc6;}</style>"

    return _old(reviewer) + js + style


def myRevBottomHTML(reviewer, _old):
    ctrl = bool_to_str(config["ctrl_click"])
    script = BOTTOMJS % ({"ctrl": ctrl})

    return _old(reviewer) + script


def edit(txt, extra, context, field, fullname):
    ctrl = bool_to_str(config["ctrl_click"])

    # Encode field to escape special characters.
    field = base64.b64encode(field.encode('utf-8')).decode('ascii')
    txt = """<%s data-EFDRCfield="%s" data-EFDRC="true">%s</%s>""" % (
        config['tag'], field, txt, config['tag'])
    txt += CARDJS % ({"fld": field})
    return txt


def saveField(note, fld, val):
    if fld == "Tags":
        tagsTxt = unicodedata.normalize("NFC", htmlToTextLine(val))
        txt = mw.col.tags.canonify(mw.col.tags.split(tagsTxt))
        field = note.tags
    else:
        # aqt.editor.Editor.onBridgeCmd
        txt = unicodedata.normalize("NFC", val)
        txt = Editor.mungeHTML(None, txt)
        txt = txt.replace("\x00", "")
        txt = mw.col.media.escapeImages(txt, unescape=True)
        field = note[fld]
    if field == txt:
        return

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
            tooltip(ERROR_MSG % fld)
        orig_val = note[fld]
        orig_enc_val = base64.b64encode(
            orig_val.encode('utf-8')).decode('ascii')
        if enc_val == orig_enc_val:  # enc_val may be the val of prev reviewed card.
            saveThenRefreshFld(reviewer, note, fld, new_val)
        else:
            tooltip(ERROR_MSG % fld)

    # Replace reviewer field html if it is different from real field value.
    # For example, clozes, mathjax, audio.
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
                $(elem).find("img").each(resizeImage);
            }
        }
        """ % (encoded_val, fld))

        # Reset timer from Speed Focus Mode add-on.
        reviewer.bottom.web.eval("""
            if (typeof autoAnswerTimeout !== 'undefined') {
                clearTimeout(autoAnswerTimeout);
            }
            if (typeof autoAlertTimeout !== 'undefined') {
                clearTimeout(autoAlertTimeout);
            }
            if (typeof autoAgainTimeout !== 'undefined') {
                clearTimeout(autoAgainTimeout);
            }
        """)
        
    elif url == "EFDRC!reload":
        if reviewer.state == "question":
            reviewer._showQuestion()
        elif reviewer.state == "answer":
            reviewer._showAnswer()

    # Catch ctrl key presses from bottom.web.
    elif url == "EFDRC!ctrldown":
        reviewer.web.eval("EFDRC.ctrldown()")
    elif url == "EFDRC!ctrlup":
        reviewer.web.eval("EFDRC.ctrlup()")

    elif url == "EFDRC!paste":
        # From aqt.editor.Editor._onPaste, doPaste.
        mime = mw.app.clipboard().mimeData(mode=QClipboard.Clipboard)
        html, internal = editorwv._processMime(mime)
        html = editorwv.editor._pastePreFilter(html, internal)
        reviewer.web.eval("pasteHTML(%s, %s);" %
                          (json.dumps(html), json.dumps(internal)))

    elif url.startswith("EFDRC!debug#"):
        fld = url.replace("EFDRC!debug#", "")
        showText(fld)
    else:
        return _old(reviewer, url)


Reviewer._bottomHTML = wrap(Reviewer._bottomHTML, myRevBottomHTML, "around")
Reviewer.revHtml = wrap(Reviewer.revHtml, myRevHtml, "around")
Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
addHook('fmod_edit', edit)
