window.EFDRC = {}

EFDRC.CTRL = "%(ctrl)s"; //bool
EFDRC.PASTE = "%(paste)s"; //bool
EFDRC.SPAN = "%(span)s"; //bool
EFDRC.REMSPAN = "%(remove_span)s"; //bool
EFDRC.SPECIAL = JSON.parse(`%(special)s`) //array of array

//wrappedExceptForWhitespace, wrapInternal from /anki/editor.ts
EFDRC.wrappedExceptForWhitespace = function(text, front, back) {
    var match = text.match(/^(\s*)([^]*?)(\s*)$/);
    return match[1] + front + match[2] + back + match[3];
}

EFDRC.wrapInternal = function(front, back) {
    if (document.activeElement.dir === "rtl") {
        front = "&#8235;" + front + "&#8236;";
        back = "&#8235;" + back + "&#8236;";
    }
    const s = window.getSelection();
    let r = s.getRangeAt(0);
    const content = r.cloneContents();
    const span = document.createElement("span");
    span.appendChild(content);
    const new_ = EFDRC.wrappedExceptForWhitespace(span.innerText, front, back);
    document.execCommand("inserttext", false, new_);
    if (!span.innerHTML) {
        // run with an empty selection; move cursor back past postfix
        r = s.getRangeAt(0);
        r.setStart(r.startContainer, r.startOffset - back.length);
        r.collapse(true);
        s.removeAllRanges();
        s.addRange(r);
    }
}

EFDRC.b64DecodeUnicode = function(str) {
    return decodeURIComponent(atob(str).split('').map(function(c) {
        return '%%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
}

EFDRC.removeSpan = function(el){
    //removes all span code because depending on the note type
    //pressing backspace can wrap the text in span and apply different styling.
    var elems = el.getElementsByTagName("span");
    for(var x = 0; x < elems.length; x++){
        var span = elems[x];
        var children = span.childNodes;
        for(var y = 0; y < children.length; y++){
            //insert after node so caret position is maintained. If last sibling, inserted at end.
            span.parentNode.insertBefore(children[y], span.nextSibling); 
        }
        span.parentNode.removeChild(span);
    }
}

EFDRC.handlePaste = function(e){
    var mimetype = ["text/html", "image/", "video/", "audio/", "application/"];
    var paste = (e.clipboardData || window.clipboardData);
    for(var x = 0; x < paste.types.length; x++){
        var mtype = paste.types[x];
        var to_send = false;
        for(var y = 0; y < mimetype.length; y++){
            if(mtype.indexOf(mimetype[y]) != -1){
                to_send = true;
                break;
            }
        }
        if(to_send){
            e.preventDefault();
            pycmd("EFDRC!paste"); //python code accesses clipboard
            break;
        }
    }
}    

EFDRC.ctrldown = function(){
    els = document.querySelectorAll("[data-EFDRC='true']"); 
    for(var e = 0; e < els.length; e++){
        var el = els[e];
        el.setAttribute("contenteditable", "true");
        if(el.hasAttribute("data-EFDRCnotctrl")){
            el.removeAttribute("data-EFDRCnotctrl");
        }
    }
}

EFDRC.ctrlup = function(){
    var els = document.querySelectorAll("[data-EFDRC='true']");
    for(var e = 0; e < els.length; e++){
        var el = els[e];
        if(el == document.activeElement){
            el.setAttribute("data-EFDRCnotctrl", "true");
        }else{
            el.setAttribute("contenteditable", "false");
        }
    }
}

EFDRC.addListeners = function(e, fld){
    if(EFDRC.PASTE){
        e.addEventListener('paste', EFDRC.handlePaste);
    }

    e.addEventListener('focus', function(event){
        pycmd("EFDRC!focuson#" + fld);
    })

    e.addEventListener('blur',function(event){
        var el = event.currentTarget;
        if(EFDRC.REMSPAN){
            EFDRC.removeSpan(el);
        }
        if(el.hasAttribute("data-EFDRCnotctrl")){
            el.removeAttribute("data-EFDRCnotctrl");
            el.setAttribute("contenteditable", "false");
        }
        if(el.hasAttribute("data-EFDRCval")){
            pycmd("EFDRC#" + el.getAttribute("data-EFDRCval") + "#" + el.getAttribute("data-EFDRCfield") + "#" + el.innerHTML);
            pycmd("EFDRC!reload");
        }else{
            pycmd("EFDRC!reload");
        }
    })


    e.addEventListener('keydown',function(event){
        //Slightly faster.
        var ctrlKey = event.ctrlKey||event.metaKey
        var shiftKey = event.shiftKey;
        var altKey = event.altKey;
        var codeKey = event.code;
        var el = event.currentTarget;
        if(EFDRC.SPAN){
            if (codeKey == "Backspace") {
                event.stopPropagation();
            }
        }
        if(EFDRC.REMSPAN){
            if(codeKey == "Backspace"||codeKey == "Delete"){
                setTimeout(function(){
                    EFDRC.removeSpan(el);
                }, 0)
            }
        }

        var specials_noctrl = {
            //shift, alt, key, command, has arg?
            "strikethrough": [true, true, "Digit5", "strikeThrough", false],
            "fontcolor": [false, false, "F7", "foreColor", true]
        };

        var specials_ctrl = {
            //shift, alt, key, command, has arg
            "removeformat": [false, false, "KeyR", "removeFormat", false],
            "highlight": [true, false, "KeyB", "hiliteColor", true],
            "subscript": [false, false, "Equal", "subscript", false],
            "superscript": [true, false, "Equal", "superscript", false],
            "formatblock": [false, false, "Period", "formatBlock", true],
            "hyperlink": [true, false, "KeyH", "createLink", false],
            "unhyperlink": [true, true, "KeyH", "createLink", false],
            "unorderedlist": [false, false, "BracketLeft", "insertUnorderedList", false],
            "orderedlist": [false, false, "BracketRight", "insertOrderedList", false],
            "indent": [true, false, "BracketRight", "indent", false],
            "outdent": [true, false, "BracketLeft", "outdent", false],
            "justifyCenter": [true, true, "KeyS", "justifyCenter", false],
            "justifyLeft": [true, true, "KeyL", "justifyLeft", false],
            "justifyRight": [true, true, "KeyR", "justifyRight", false],
            "justifyFull": [true, true, "KeyB", "justifyFull", false],
        };

        if(ctrlKey){
            //cloze deletion, onCloze from aqt.editor
            if(event.code == "KeyC" && shiftKey){
                var highest = 0;
                var val = el.innerHTML;
                var m;
                var myRe = /\{\{c(\d+)::/g;
                while ((m = myRe.exec(val)) !== null) {
                    highest = Math.max(highest, m[1]);
                }
                if(!altKey){
                    highest += 1;
                } 
                var highest = Math.max(1, highest);
                EFDRC.wrapInternal("{\{c" + highest + "::", "}\}");
            }

            //Special formatting that requires ctrl key.
            for(var special in specials_ctrl){
                specialVal = specials_ctrl[special]
                if(specialVal[4]){
                    var enabled = EFDRC.SPECIAL[special][0]
                    var parmVal = EFDRC.SPECIAL[special][1]
                }else{
                    var enabled = EFDRC.SPECIAL[special]
                }
                if(enabled){
                    var s = specialVal[0];
                    var a = specialVal[1];
                    var c = specialVal[2];
                    if(shiftKey == s && altKey == a && codeKey == c){
                        if(specialVal[4]){
                            document.execCommand(specialVal[3], false, parmVal);
                        }else{
                            document.execCommand(specialVal[3], false);
                        }
                        event.preventDefault();
                    }
                }
            }
        }else{
            //Special formatting that doesn't require ctrl key
            for(var special in specials_noctrl){
                specialVal = specials_noctrl[special]
                if(specialVal[4]){
                    var enabled = EFDRC.SPECIAL[special][0]
                    var parmVal = EFDRC.SPECIAL[special][1]
                }else{
                    var enabled = EFDRC.SPECIAL[special]
                }
                if(enabled){
                    var s = specialVal[0];
                    var a = specialVal[1];
                    var c = specialVal[2];
                    if(shiftKey == s && altKey == a && codeKey == c){
                        if(specialVal[4]){
                            document.execCommand(specialVal[3], false, parmVal);
                        }else{
                            document.execCommand(specialVal[3], false);
                        }
                        event.preventDefault();
                    }
                }
            }
        }

    })
}

if(EFDRC.CTRL){
    window.addEventListener('keydown',function(event){
        if(["ControlLeft", "MetaLeft"].includes(event.code)){
            EFDRC.ctrldown();
        }   
    })

    window.addEventListener('keyup',function(event){
        if(["ControlLeft", "MetaLeft"].includes(event.code)){
            EFDRC.ctrlup();
        }    
    })
}
