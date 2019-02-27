# -*- coding: utf-8 -*-

"""
Anki Add-on: Edit Field During Review

Edit text in a field during review without opening the edit window

Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
"""

from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from aqt.clayout import CardLayout
from aqt import mw, dialogs

import unicodedata

def edit(txt, extra, context, field, fullname):
    config = mw.addonManager.getConfig(__name__)
    txt = """<%s contenteditable="true" data-field="%s">%s</%s>""" % (config['tag'], field, txt, config['tag'])
    txt += """<script>"""
    txt += """
            $("[contenteditable=true][data-field='%s']").blur(function() {
                pycmd("ankisave#" + $(this).data("field") + "#" + $(this).html());
            });
        """ % field
    if config['tag'] == "span":
        txt += """
            $("[contenteditable=true][data-field='%s']").keydown(function(evt) {
                if (evt.keyCode == 8) {
                    evt.stopPropagation();
                }
            });
        """ % field
    txt += """
            $("[contenteditable=true][data-field='%s']").focus(function() {
                pycmd("ankisave!speedfocus#");
            });
        """ % field
    txt += """</script>"""
    return txt

addHook('fmod_edit', edit)

def saveField(note, fld, val):
    mw.checkpoint("Edit Field")
    if fld == "Tags":
        tagsTxt = unicodedata.normalize("NFC", htmlToTextLine(val))
        note.tags = mw.col.tags.canonify(mw.col.tags.split(tagsTxt))
    else:
        note[fld] = mw.col.media.escapeImages(val, unescape=True)
    note.flush()

def myLinkHandler(reviewer, url):
    if url.startswith("ankisave#"):
        fld, val = url.replace("ankisave#", "").split("#", 1)
        note = reviewer.card.note()
        saveField(note, fld, val)
        reviewer.card.q(reload=True)
    elif url.startswith("ankisave!speedfocus#"):
        mw.reviewer.bottom.web.eval("""
            clearTimeout(autoAnswerTimeout);
            clearTimeout(autoAlertTimeout);
            clearTimeout(autoAgainTimeout);
        """)
    else:
        origLinkHandler(reviewer, url)

origLinkHandler = Reviewer._linkHandler
Reviewer._linkHandler = myLinkHandler

def onOpenCardLayout(self, *args, **kwargs):
    mw.cardLayout = self

def onCloseCardLayout(self):
    mw.cardLayout = None

CardLayout.__init__ = wrap(CardLayout.__init__, onOpenCardLayout, "after")
CardLayout.reject = wrap(CardLayout.reject, onCloseCardLayout, "after")

def myBridgeCmd(self, cmd, _old):
    if cmd.startswith("ankisave#"):
        browser = dialogs._dialogs['Browser'][1]
        cardLayout = getattr(mw, "cardLayout", None)
        if cardLayout is None and browser is not None:
            fld, val = cmd.replace("ankisave#", "").split("#", 1)
            note = browser.card.note()
            saveField(note, fld, val)
            browser.editor.setNote(note)
            if mw.state == "review" and mw.reviewer.card.id == browser.card.id:
                mw.requireReset()
    else:
        _old(self, cmd)

AnkiWebView.defaultOnBridgeCmd = wrap(AnkiWebView.defaultOnBridgeCmd, myBridgeCmd, "around")
