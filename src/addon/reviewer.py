import base64
import json
from typing import Any, Optional, Tuple, Union

import anki
from anki.template import TemplateRenderContext
from anki.notes import Note
from anki.cards import Card
from anki.collection import OpChanges
import aqt
from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.qt import QClipboard
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.browser.previewer import MultiCardPreviewer
from aqt.utils import showText, tooltip
from aqt.operations.note import update_note

from .semieditor import SemiEditorWebView
from .ankiaddonconfig import ConfigManager

ERROR_MSG = "ERROR - Edit Field During Review Cloze\n{}"

editorwv = SemiEditorWebView()


class FldNotFoundError(Exception):
    def __init__(self, fld: str):
        self.fld = fld

    def __str__(self) -> str:
        return f"Field {self.fld} not found in note. Please check your note type."


conf = ConfigManager()


def myRevHtml() -> str:
    conf.load()  # update config when reviewer is launched

    # config should not have any single quote values
    js = "EFDRC.registerConfig('{}');".format(conf.to_json())
    js += "EFDRC.setupReviewer()"
    return f"<script>{js}</script>"


def edit_filter(txt: str, field: str, filt: str, ctx: TemplateRenderContext) -> str:
    if not filt == "edit":
        return txt
    # Encode field to escape special characters.
    class_name = ""
    if conf["outline"]:
        class_name += "EFDRC-outline "
    if conf["ctrl_click"]:
        class_name += "EFDRC-ctrl "
    field = base64.b64encode(field.encode("utf-8")).decode("ascii")
    txt = """<%s data-EFDRCfield="%s" class="%s">%s</%s>""" % (
        conf["tag"],
        field,
        class_name,
        txt,
        conf["tag"],
    )
    return txt


def serve_card(txt: str, card: Card, kind: str) -> str:
    return txt + "<script>EFDRC.serveCard()</script>"


def save_field_and_reload(
        note: Note, 
        fld: str, 
        val: str, 
        context: Union[Reviewer, MultiCardPreviewer]
) -> None:
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
    # 2.1.45+

    def on_success(changes: OpChanges) -> None:
        reload_review_context(context)
    
    def on_failure(exc: Exception) -> None:
        reload_review_context(context)
        raise exc

    update_note(
        parent=mw, note=note
    ).success(on_success).failure(on_failure).run_in_background()


def get_value(note: Note, fld: str) -> str:
    if fld == "Tags":
        try:
            string_tags = note.string_tags()
        except:
            string_tags = note.stringTags() # type:ignore
        return string_tags.strip(" ")
    if fld in note:
        return note[fld]
    raise FldNotFoundError(fld)


def reload_reviewer(reviewer: Reviewer) -> None:
    cid = reviewer.card.id
    try:
        timer_started = reviewer.card.timer_started
        timer_started_snake_case = True
    except:
        timer_started = reviewer.card.timerStarted  # type: ignore
        timer_started_snake_case = False
    reviewer.card = mw.col.getCard(cid) # type: ignore
    if timer_started_snake_case:
        reviewer.card.timer_started = timer_started
    else:
        reviewer.card.timerStarted = timer_started  # type: ignore

    if reviewer.state == "question":
        reviewer._showQuestion()
    elif reviewer.state == "answer":
        reviewer._showAnswer()

def reload_previewer(previewer: MultiCardPreviewer) -> None:
    # previewer may skip rendering if modified note's mtime has not changed
    previewer._last_state = None
    previewer.render_card()

def reload_review_context(context: Union[Reviewer, MultiCardPreviewer]) -> None:
    if isinstance(context, Reviewer):
        reload_reviewer(context)
    else:
        reload_previewer(context)

def handle_pycmd_message(
    handled: Tuple[bool, Any], message: str, context: Any
) -> Tuple[bool, Any]:
    if isinstance(context, Reviewer):
        card = context.card
        web: "aqt.webview.AnkiWebView" = context.web
        reviewer = context
        previewer = None
    elif isinstance(context, MultiCardPreviewer):
        if context._web is None:
            return handled
        card = context.card()
        web = context._web        
        reviewer = None
        previewer = context
    else:
        return handled

    if message.startswith("EFDRC#"):
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nidstr, fld, new_val = message.replace("EFDRC#", "").split("#", 2)
        nid = int(nidstr)
        note = card.note()
        if note.id != nid:
            # nid may be note id of previous reviewed card
            tooltip(ERROR_MSG.format(errmsg))
            return (True, None)
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        try:
            save_field_and_reload(note, fld, new_val, context)
            return (True, None)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)

    # Replace reviewer field html if it is different from real field value.
    # For example, clozes, mathjax, audio.
    elif message.startswith("EFDRC!focuson#"):
        fld = message.replace("EFDRC!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode("utf-8")
        note = card.note()
        try:
            val = get_value(note, decoded_fld)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)
        encoded_val = base64.b64encode(val.encode("utf-8")).decode("ascii")
        web.eval(f"EFDRC.showRawField('{encoded_val}', '{note.id}', '{fld}')")

        # Reset timer from Speed Focus Mode add-on.
        if reviewer is not None:
            reviewer.bottom.web.eval("window.EFDRCResetTimer()")
        return (True, None)

    elif message == "EFDRC!reload":
        reload_review_context(context)
        return (True, None)
        # Catch ctrl key presses from bottom.web.
    elif message == "EFDRC!ctrldown":
        web.eval("EFDRC.ctrldown()")
        return (True, None)
    elif message == "EFDRC!ctrlup":
        web.eval("EFDRC.ctrlup()")
        return (True, None)

    elif message == "EFDRC!paste":
        # From aqt.editor.Editor._onPaste, doPaste.
        mime = mw.app.clipboard().mimeData(mode=QClipboard.Mode.Clipboard)
        html, internal = editorwv._processMime(mime)
        print(internal)
        html = editorwv.editor._pastePreFilter(html, internal)
        print(html)
        web.eval(
            "EFDRC.pasteHTML(%s, %s);" % (json.dumps(html), json.dumps(internal))
        )
        return (True, None)

    elif message.startswith("EFDRC!debug#"):
        fld = message.replace("EFDRC!debug#", "")
        showText(fld)
        return (True, None)
    return handled


def url_from_fname(file_name: str) -> str:
    addon_package = mw.addonManager.addonFromModule(__name__)
    return f"/_addons/{addon_package}/web/{file_name}"


def on_webview(web_content: aqt.webview.WebContent, context: Optional[Any]) -> None:
    if isinstance(context, Reviewer) or isinstance(context, MultiCardPreviewer):
        web_content.body += myRevHtml()
        web_content.body += f'<script type="module" src="{url_from_fname("editor/editor.js")}"></script>'
        js_contents = ["global_card.js", "resize.js"]
        for file_name in js_contents:
            web_content.js.append(url_from_fname(file_name))
        jquery_ui = "js/vendor/jquery-ui.min.js"
        if jquery_ui not in web_content.js:
            web_content.js.append(jquery_ui)
        web_content.css.append(url_from_fname("global_card.css"))

    elif isinstance(context, ReviewerBottomBar):
        web_content.js.append(url_from_fname("bottom.js"))


mw.addonManager.setWebExports(__name__, r"web/.*")
gui_hooks.webview_will_set_content.append(on_webview)
gui_hooks.webview_did_receive_js_message.append(handle_pycmd_message)
gui_hooks.card_will_show.append(serve_card)
anki.hooks.field_filter.append(edit_filter)
