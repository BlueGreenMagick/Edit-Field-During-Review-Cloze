//Capital EFDRC is just for easier code reading. Case doesn't matter.

CTRL = %(ctrl)s; //bool
PASTE = %(paste)s; //bool
SPAN = %(span)s;
BR_NEWLINE = %(br_newline)s; //bool
FLD = "%(fld)s"; //string

//wrappedExceptForWhitespace, wrapInternal from /anki/editor.ts
if(typeof wrappedExceptForWhitespace != "function"){
    window.wrappedExceptForWhitespace = function(text, front, back) {
        var match = text.match(/^(\s*)([^]*?)(\s*)$/);
        return match[1] + front + match[2] + back + match[3];
    }

    window.wrapInternal = function(front, back) {
        if (document.activeElement.dir === "rtl") {
            front = "&#8235;" + front + "&#8236;";
            back = "&#8235;" + back + "&#8236;";
        }
        const s = window.getSelection();
        let r = s.getRangeAt(0);
        const content = r.cloneContents();
        const span = document.createElement("span");
        span.appendChild(content);
        const new_ = wrappedExceptForWhitespace(span.innerText, front, back);
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
    window.b64DecodeUnicode = function(str) {
        return decodeURIComponent(atob(str).split('').map(function(c) {
            return '%%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
    }
    
    window.EFDRCctrldown = function(){
        els = document.querySelectorAll("[data-EFDRC='true']"); 
        for(var e = 0; e < els.length; e++){
            var el = els[e];
            el.setAttribute("contenteditable", "true");
            if(el.hasAttribute("data-EFDRCnotctrl")){
                el.removeAttribute("data-EFDRCnotctrl");
            }
        }
    }

    window.EFDRCctrlup = function(){
        els = document.querySelectorAll("[data-EFDRC='true']");
        for(var e = 0; e < els.length; e++){
            var el = els[e];
            if(el == document.activeElement){
                el.setAttribute("data-EFDRCnotctrl", "true");
            }else{
                el.setAttribute("contenteditable", "false");
            }
        }
    }

    window.handlePaste = function(e){
        var mimetype = ["text/html", "image/", "video/", "audio/", "application/"];
        var paste = (e.clipboardData || window.clipboardData);
        for(var x = 0; x < paste.types.length; x++){
            mtype = paste.types[x];
            to_send = false;
            for(var y = 0; y < mimetype.length; y++){
                if(mtype.indexOf(mimetype[y]) != -1){
                    to_send = true;
                    break;
                }
            }
            if(to_send){
                e.preventDefault();
                pycmd("EFDRC#paste");
                break;
            }
        }
        
    }

    window.EFDRCaddListeners = function(e, fld){
        if(PASTE){
            e.addEventListener('paste', handlePaste);
        }

        e.addEventListener('focus', function(event){
            pycmd("ankisave!focuson#" + fld);
            pycmd("ankisave!speedfocus#");
        })

        e.addEventListener('blur',function(event){
            var el = event.currentTarget;
            if(el.hasAttribute("data-EFDRCnotctrl")){
                el.removeAttribute("data-EFDRCnotctrl");
                el.setAttribute("contenteditable", "false");
            }
            if(el.hasAttribute("data-EFDRCval")){
                pycmd("ankisave#" + el.getAttribute("data-EFDRCval") + "#" + el.getAttribute("data-EFDRCfield") + "#" + el.innerHTML);
                pycmd("ankisave!reload");
            }else{
                pycmd("ankisave!reload");
            }
        })
        
        e.addEventListener('keyup', function(event){
            var el = event.currentTarget;
            if (!el.lastChild || el.lastChild.nodeName.toLowerCase() != "br") {
                el.appendChild(document.createElement("br"));
            }
        })

        e.addEventListener('mouseup', function(event){
            var el = event.currentTarget;
            if (!el.lastChild || el.lastChild.nodeName.toLowerCase() != "br") {
                el.appendChild(document.createElement("br"));
            }
        })


        e.addEventListener('keydown',function(event){
            //onCloze from /aqt/editor.py
            var el = event.currentTarget;
            if(event.code == "KeyC" && event.shiftKey && (event.ctrlKey||event.metaKey)){
                var highest = 0;
                var val = el.innerHTML;
                var m;
                var myRe = /\{\{c(\d+)::/g;
                while ((m = myRe.exec(val)) !== null) {
                    highest = Math.max(highest, m[1]);
                }
                if(!event.altKey){
                    highest += 1;
                } 
                var highest = Math.max(1, highest);
                wrapInternal("{\{c" + highest + "::", "}\}");
            }
            if(SPAN){
                if (event.code == "Backspace") {
                    event.stopPropagation();
                }
            }

            if(BR_NEWLINE && event.code == "Enter"){
                br = document.createElement("br")
                event.preventDefault();
                selection = window.getSelection();
                range = selection.getRangeAt(0);
                range.deleteContents();
                range.insertNode(br);
                range.setStartAfter(br);
                range.setEndAfter(br);
                selection.removeAllRanges();
                selection.addRange(range);
            }


        })
    }
    if(CTRL){
        window.addEventListener('keydown',function(event){
            if(event.code == "ControlLeft"){
                EFDRCctrldown();
            }   
        })

        window.addEventListener('keyup',function(event){
            if(event.keyCode == "ControlLeft"){
                EFDRCctrlup();
            }    
        })

    }
}

els = document.querySelectorAll("[data-EFDRCfield='"+ FLD +"']");
for(var e = 0; e < els.length; e++){
    var el = els[e];
    EFDRCaddListeners(el, FLD);
}

if(!CTRL){
    for(var e = 0; e < els.length; e++){
        els[e].setAttribute("contenteditable", "true");
    }
}
