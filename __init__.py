# -*- coding: utf-8 -*-

"""
Anki Add-on: Edit Field During Review
Edit text in a field during review without opening the edit window
Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
"""

from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from aqt.editor import Editor
from aqt.reviewer import Reviewer
from aqt import mw

import base64
import unicodedata
import urllib.parse


def edit(txt, extra, context, field, fullname):
    config = mw.addonManager.getConfig(__name__)
    field = base64.b64encode(field.encode('utf-8')).decode('ascii')
    txt = """<%s contenteditable="true" data-field="%s">%s</%s>""" % (
        config['tag'], field, txt, config['tag'])
    txt += """<script>"""
    txt += """
            $("[contenteditable=true][data-field='%(fld)s']").focus(function(){
                pycmd("ankisave!focuson#%(fld)s");
            })
            $("[contenteditable=true][data-field='%(fld)s']").blur(function(){
                pycmd("ankisave#" + $(this).data("field") + "#" + $(this).html());
                pycmd("ankisave!focusoff#%(fld)s");
            })  
            """ % {"fld": field}
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
    fld = base64.b64decode(fld, validate=True).decode('utf-8')
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


def myLinkHandler(reviewer, url, _old):
    if url.startswith("ankisave#"):
        fld, val = url.replace("ankisave#", "").split("#", 1)
        note = reviewer.card.note()
        saveField(note, fld, val)
        reviewer.card.q(reload=True)
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
        if(!b64DecodeUnicode){
            function b64DecodeUnicode(str) {
                return decodeURIComponent(atob(str).split('').map(function(c) {
                    return '%%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join(''));
            }
        }
        var val = b64DecodeUnicode("%s")
        elem = document.querySelector("[contenteditable=true][data-field='%s']")
        if(elem.innerHTML != val){
            elem.innerHTML = val
        }
        """ % (encoded_val, fld))
    elif url.startswith("ankisave!focusoff#"):
        if reviewer.state == "question":
            reviewer._showQuestion()
        elif reviewer.state == "answer":
            reviewer._showAnswer()
    else:
        return _old(reviewer, url)


Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
