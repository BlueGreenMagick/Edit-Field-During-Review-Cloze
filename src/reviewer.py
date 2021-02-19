import base64
import json
import unicodedata
from pathlib import Path
from typing import Any, Optional

from anki import version as ankiversion
from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
import aqt
from aqt import mw, gui_hooks
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


class FldNotFoundError(Exception):
    def __init__(self, fld):
        self.fld = fld

    def __str__(self) -> str:
        return f"Field {self.fld} not found in note. Please check your note type."


# Code for new style hooks.
def new_fld_hook(txt, field, filt, ctx):
    if filt == "edit":
        return edit(txt, None, None, field, None)


# from anki import hooks
# hooks.field_filter.append(new_fld_hook)


def myRevHtml():
    global config  # update config when reviewer is launched
    config = mw.addonManager.getConfig(__name__)
    config_make_valid(config)

    # config should not have any single quote values
    js = "EFDRC.registerConfig('{}')".format(json.dumps(config))
    return f"<script>{js}</script>"


def edit(txt, extra, context, field, fullname):
    # Encode field to escape special characters.
    class_name = ""
    if config["outline"]:
        class_name += "EFDRC-outline "
    if config["ctrl_click"]:
        class_name += "EFDRC-ctrl "
    field = base64.b64encode(field.encode("utf-8")).decode("ascii")
    txt = """<%s data-EFDRCfield="%s" data-EFDRC="true" class="%s">%s</%s>""" % (
        config["tag"],
        field,
        class_name,
        txt,
        config["tag"],
    )
    txt += "<script>EFDRC.serveCard('{}')</script>".format(field)
    return txt


def saveField(note, fld, val):
    if fld == "Tags":
        # aqt.editor.Editor.saveTags
        tags = mw.col.tags.split(val)
        if note.tags == tags:
            return
        note.tags = tags
    elif fld not in note:
        raise FldNotFoundError(fld)
    else:
        # aqt.editor.Editor.onBridgeCmd
        txt = Editor.mungeHTML(editorwv.editor, val)
        if note[fld] == txt:
            return
        note[fld] = txt
    if config["undo"]:
        mw.checkpoint("Edit Field")
    note.flush()


def get_value(note, fld):
    if fld == "Tags":
        return note.stringTags().strip(" ")
    if fld in note:
        return note[fld]
    raise FldNotFoundError(fld)


def reload_reviewer(reviewer: aqt.reviewer.Reviewer):
    cid = reviewer.card.id
    timerStarted = reviewer.card.timerStarted
    reviewer.card = mw.col.getCard(cid)
    reviewer.card.timerStarted = timerStarted
    if reviewer.state == "question":
        reviewer._showQuestion()
    elif reviewer.state == "answer":
        reviewer._showAnswer()


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
            saveField(note, fld, new_val)
            reload_reviewer(reviewer)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return

    # Replace reviewer field html if it is different from real field value.
    # For example, clozes, mathjax, audio.
    elif url.startswith("EFDRC!focuson#"):
        fld = url.replace("EFDRC!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode("utf-8")
        note = reviewer.card.note()
        try:
            val = get_value(note, decoded_fld)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
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
        reviewer.bottom.web.eval("window.EFDRCResetTimer()")

    elif url == "EFDRC!reload":
        reload_reviewer(reviewer)
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


def url_from_fname(file_name: str) -> str:
    addon_package = mw.addonManager.addonFromModule(__name__)
    return f"/_addons/{addon_package}/web/{file_name}"


def on_webview(web_content: aqt.webview.WebContent, context: Optional[Any]):

    if isinstance(context, aqt.reviewer.Reviewer):
        web_content.body += myRevHtml()
        js_contents = ["global_card.js", "resize.js", "jquery-ui.min.js"]
        if config["process_paste"]:
            js_contents.append("paste.js")
        for file_name in js_contents:
            web_content.js.append(url_from_fname(file_name))
        web_content.css.append(url_from_fname("global_card.css"))

    elif isinstance(context, aqt.reviewer.ReviewerBottomBar):
        web_content.js.append(url_from_fname("bottom.js"))


mw.addonManager.setWebExports(__name__, r"web/.*")
gui_hooks.webview_will_set_content.append(on_webview)
Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
addHook("fmod_edit", edit)

# gui_hooks.card_will_show.append(lambda t, c, k: print(t))
