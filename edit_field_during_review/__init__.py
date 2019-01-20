# -*- coding: utf-8 -*-

"""
Anki Add-on: Edit Field During Review

Edit text in a field during review without opening the edit window

Copyright: (c) 2019 Nickolay <kelciour@gmail.com>
"""

from anki.hooks import addHook, wrap
from aqt.reviewer import Reviewer
from aqt import mw

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

def myLinkHandler(reviewer, url):
    if url.startswith("ankisave#"):
        fld, val = url.replace("ankisave#", "").split("#", 1)
        reviewer.card.note()[fld] = val
        reviewer.card.note().flush()
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
