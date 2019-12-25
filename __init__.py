# -*- coding: utf-8 -*-

"""
Anki Add-on: Edit Field During Review Cloze
Edit text in a field during review without opening the edit window
Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
Modified by <bluegreenmagick@gmail.com>
"""

from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine
from aqt.editor import Editor
from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from aqt import mw

import base64
import unicodedata
import urllib.parse


card_js ="""
<script>
function addListeners(e){
    e.addEventListener('mousedown',function(event){
        var el = event.currentTarget
        if(%(ctrl)s&&!event.ctrlKey){
            if(el != document.activeElement){
                el.setAttribute("data-EFDRCdontfocus","true");
            }
        }
    })
    e.addEventListener('focus', function(event){
        var el = event.currentTarget
        if(el.getAttribute("data-EFDRCdontfocus") == "true"){
            el.blur()
        }else{
            pycmd("ankisave!focuson#%(fld)s");
            pycmd("ankisave!speedfocus#");
        }
    })
    e.addEventListener('blur',function(event){
        var el = event.currentTarget;
        if(el.getAttribute("data-EFDRCdontfocus") == "true"){
            el.setAttribute("data-EFDRCdontfocus","false"); 
        }else if(el.hasAttribute("data-EFDRCval")){
            pycmd("ankisave#" + el.getAttribute("data-EFDRCval") + "#" + el.getAttribute("data-EFDRCfield") + "#" + el.innerHTML);
            pycmd("ankisave!reload");
        }else{
            pycmd("ankisave!reload");
        }
    })
    if(%(span)s){
        el.addEventListener('keydown', function(event){
            if (event.keyCode == 8) {
                event.stopPropagation();
            }
        })
    }
}
var els = document.querySelectorAll("[contenteditable=true][data-EFDRCfield='%(fld)s']");
for(var e = 0; e < els.length; e++){
    var el = els[e];
    addListeners(el)
}
</script>
"""


def edit(txt, extra, context, field, fullname):
    config = mw.addonManager.getConfig(__name__)
    if config['tag'] == "span":
        span = "true"
    else:
        span = "false"
    if config["ctrl_click"]:
        ctrl = "true"
    else:
        ctrl = "false"
    field = base64.b64encode(field.encode('utf-8')).decode('ascii')
    txt = """<%s contenteditable="true" data-EFDRCfield="%s" data-EFDRCdontfocus="false">%s</%s>""" % (
        config['tag'], field, txt, config['tag'])
    txt += card_js % ({"fld":field, "span":span, "ctrl":ctrl})
    return txt


addHook('fmod_edit', edit)


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


def myLinkHandler(reviewer, url, _old):
    if url.startswith("ankisave#"):
        enc_val, fld, new_val = url.replace("ankisave#", "").split("#", 2)
        note = reviewer.card.note()
        fld = base64.b64decode(fld, validate=True).decode('utf-8')
        orig_val = note[fld]
        orig_enc_val = base64.b64encode(orig_val.encode('utf-8')).decode('ascii')
        if enc_val == orig_enc_val: #enc_val may be the val of prev reviewed card.
            saveField(note, fld, new_val)
            reviewer.card.q(reload=True)
        else:
            tooltip("ERROR - Edit Field During Review Cloze\nSomething unexpected occured. The edit was not saved.%s"%fld)
            
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
        var encoded_val = "%s"
        var val = b64DecodeUnicode(encoded_val)
        var elems = document.querySelectorAll("[contenteditable=true][data-EFDRCfield='%s']")
        for(var e = 0; e < elems.length; e++){
            var elem = elems[e]
            elem.setAttribute("data-EFDRCval", encoded_val)
            if(elem.innerHTML != val){
                elem.innerHTML = val
            }
        }
        """ % (encoded_val, fld))
    elif url.startswith("ankisave!reload"):
        if reviewer.state == "question":
            reviewer._showQuestion()
        elif reviewer.state == "answer":
            reviewer._showAnswer()
    else:
        return _old(reviewer, url)


Reviewer._linkHandler = wrap(Reviewer._linkHandler, myLinkHandler, "around")
