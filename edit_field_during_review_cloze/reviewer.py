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
from .config import config_make_valid

ERROR_MSG = "ERROR - Edit Field During Review Cloze\n{}"
config = mw.addonManager.getConfig(__name__)

ankiver_minor = int(ankiversion.split(".")[2])
ankiver_major = ankiversion[0:3]

editorwv = semiEditorWebView()


# Get js files.
def js_from_path(path):
    return "<script>" + path.read_text() + "</script>"


def css_from_path(path):
    return "<style>" + path.read_text() + "</style>"


DIRPATH = Path(__file__).parents[0]
WEBPATH = DIRPATH / "web"

CARDJS = js_from_path(WEBPATH / "card.js")
GLOBALCARDJS = js_from_path(WEBPATH / "global_card.js")
RESIZEJS = js_from_path(WEBPATH / "resize.js")
JQUERYUIJS = js_from_path(WEBPATH / "jquery-ui.min.js")
RESIZECSS = css_from_path(WEBPATH / "resize.css")
PASTEJS = js_from_path(WEBPATH / "paste.js")
BOTTOMJS = js_from_path(WEBPATH / "bottom.js")


def bool_to_str(b):
    if b:
        return "true"
    else:
        return ""


# Code for new style hooks.
def new_fld_hook(txt, field, filt, ctx):
    if filt == "edit":
        return edit(txt, None, None, field, None)


# from anki import hooks
# hooks.field_filter.append(new_fld_hook)


def myRevHtml(reviewer, _old):
    global config
    config = mw.addonManager.getConfig(__name__)
    config = config_make_valid(config)

    js = ""
    css = ""

    span = bool_to_str(config["tag"])
    ctrl = bool_to_str(config["ctrl_click"])
    paste = bool_to_str(config["process_paste"])
    rem_span = bool_to_str(config["remove_span"])
    special = json.dumps(config["z_special_formatting"])
    js += GLOBALCARDJS % (
        {
            "span": span,
            "ctrl": ctrl,
            "paste": paste,
            "remove_span": rem_span,
            "special": special,
        }
    )

    preserve_ratio = config["resize_image_preserve_ratio"]
    resize_state = bool_to_str(config["resize_image_default_state"])
    css += RESIZECSS
    js += JQUERYUIJS
    js += RESIZEJS % ({"preserve_ratio": preserve_ratio, "resize_state": resize_state})

    if config["process_paste"]:
        js += PASTEJS

    if config["outline"]:
        css += "<style>[data-efdrc='true'][contenteditable='true']:focus{outline: 1px solid #308cc6;}</style>"

    # placeholder style
    if config["ctrl_click"]:
        css += "<style>[data-efdrc='true'][contenteditable='true'][data-placeholder]:empty:before {content: attr(data-placeholder);color: #888;font-style: italic;}</style>"


    return _old(reviewer) + js + css


def myRevBottomHTML(reviewer, _old):
    return _old(reviewer) + BOTTOMJS


def edit(txt, extra, context, field, fullname):
    ctrl = bool_to_str(config["ctrl_click"])

    # Encode field to escape special characters.
    field = base64.b64encode(field.encode("utf-8")).decode("ascii")
    txt = """<%s data-EFDRCfield="%s" data-EFDRC="true">%s</%s>""" % (
        config["tag"],
        field,
        txt,
        config["tag"],
    )
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

    if config["undo"]:
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


def get_value(note, fld):
    check_fld_is_valid(note, fld)
    if fld == "Tags":
        return note.stringTags().strip(" ")
    if fld in note:
        return note[fld]


def check_fld_is_valid(note, fld):
    if fld in note:
        return True
    elif fld == "Tags":
        return True
    else:
        raise KeyError(f"Field {fld} not found in note. Please check your note type.")


def myLinkHandler(reviewer, url, _old):
    if url.startswith("EFDRC#"):
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nid, fld, new_val = url.replace("EFDRC#", "").split("#", 2)
        nid = int(nid)
        note = reviewer.card.note()
        if note.id != nid:
            # nid may be note id of previous reviewed card
            tooltip(ERROR_MSG.format(errmsg))
            return
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        try:
            check_fld_is_valid(note, fld)
        except KeyError as e:
            tooltip(ERROR_MSG.format(e.message))
            return
        saveThenRefreshFld(reviewer, note, fld, new_val)

    # Replace reviewer field html if it is different from real field value.
    # For example, clozes, mathjax, audio.
    elif url.startswith("EFDRC!focuson#"):
        fld = url.replace("EFDRC!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode("utf-8")
        note = reviewer.card.note()
        try:
            val = get_value(note, decoded_fld)
        except KeyError as e:
            tooltip(ERROR_MSG.format(e.message))
            return
        encoded_val = base64.b64encode(val.encode("utf-8")).decode("ascii")
        reviewer.web.eval(
            """
        (function(){
            var encoded_val = "%s";
            var nid = %d;
            var val = EFDRC.b64DecodeUnicode(encoded_val);
            var elems = document.querySelectorAll("[data-EFDRCfield='%s']")
            for(var e = 0; e < elems.length; e++){
                var elem = elems[e];
                elem.setAttribute("data-EFDRCnid", nid);
                if(elem.innerHTML != val){
                    elem.innerHTML = val;
                }
            }
            EFDRC.maybeResizeOrClean(true);
        })()
        """
            % (encoded_val, note.id, fld)
        )

        # Reset timer from Speed Focus Mode add-on.
        reviewer.bottom.web.eval(
            """
            if (typeof autoAnswerTimeout !== 'undefined') {
                clearTimeout(autoAnswerTimeout);
            }
            if (typeof autoAlertTimeout !== 'undefined') {
                clearTimeout(autoAlertTimeout);
            }
            if (typeof autoAgainTimeout !== 'undefined') {
                clearTimeout(autoAgainTimeout);
            }
        """
        )

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
        reviewer.web.eval(
            "pasteHTML(%s, %s);" % (json.dumps(html), json.dumps(internal))
        )

    elif url.startswith("EFDRC!debug#"):
        fld = url.replace("EFDRC!debug#", "")
        showText(fld)
    else:
        return _old(reviewer, url)


Reviewer._bottomHTML = wrap(Reviewer._bottomHTML, myRevBottomHTML, "around")
Reviewer.revHtml = wrap(Reviewer.revHtml, myRevHtml, "around")
Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
addHook("fmod_edit", edit)
