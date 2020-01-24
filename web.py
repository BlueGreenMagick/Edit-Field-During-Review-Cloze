bottom_js = """
if(typeof EFDRConctrlkey != "function" && %(ctrl)s){
    window.EFDRConctrlkey = function(){
        window.addEventListener('keydown',function(event){
            if(event.keyCode == 17){
                pycmd("EFDRC#ctrldown");
            }    
        })

        window.addEventListener('keyup',function(event){
            if(event.keyCode == 17){
                pycmd("EFDRC#ctrlup");
            }    
        })        
    }
    EFDRConctrlkey()
}

"""

#mostly from anki source qt/ts/src/editor.ts
paste_js = """
<script>
  "use strict";
window.parseHTML = function(str) {
  let tmp = document.implementation.createHTMLDocument();
  tmp.body.innerHTML = str;
  return tmp.body.children;
};
window.pasteHTML = function (html, internal) {
    html = filterHTML(html, internal, false);
    document.execCommand("inserthtml", false, html);
};
window.filterHTML = function (html, internal, extendedMode) {
    // wrap it in <top> as we aren't allowed to change top level elements
    const top = parseHTML("<ankitop>" + html + "</ankitop>")[0];
    if (internal) {
        filterInternalNode(top);
    }
    else {
        filterNode(top, extendedMode);
    }
    let outHtml = top.innerHTML;
    if (!extendedMode) {
        // collapse whitespace
        outHtml = outHtml.replace(/[\\n\\t ]+/g, " ");
    }
    outHtml = outHtml.trim();
    //console.log(`input html: ${html}`);
    //console.log(`outpt html: ${outHtml}`);
    return outHtml;
};
window.allowedTagsBasic = {};
window.allowedTagsExtended = {};
window.TAGS_WITHOUT_ATTRS = ["P", "DIV", "BR", "SUB", "SUP"];
for (const tag of TAGS_WITHOUT_ATTRS) {
    allowedTagsBasic[tag] = { attrs: [] };
}
TAGS_WITHOUT_ATTRS = [
    "H1",
    "H2",
    "H3",
    "LI",
    "UL",
    "OL",
    "BLOCKQUOTE",
    "CODE",
    "PRE",
    "TABLE",
    "DD",
    "DT",
    "DL",
    "B",
    "U",
    "I",
    "RUBY",
    "RT",
    "RP",
];
for (const tag of TAGS_WITHOUT_ATTRS) {
    allowedTagsExtended[tag] = { attrs: [] };
}
allowedTagsBasic["IMG"] = { attrs: ["SRC"] };
allowedTagsExtended["A"] = { attrs: ["HREF"] };
allowedTagsExtended["TR"] = { attrs: ["ROWSPAN"] };
allowedTagsExtended["TD"] = { attrs: ["COLSPAN", "ROWSPAN"] };
allowedTagsExtended["TH"] = { attrs: ["COLSPAN", "ROWSPAN"] };
allowedTagsExtended["FONT"] = { attrs: ["COLOR"] };
window.allowedStyling = {
    color: true,
    "background-color": true,
    "font-weight": true,
    "font-style": true,
    "text-decoration-line": true,
};
window.filterExternalSpan = function (node) {
    // filter out attributes
    let toRemove = [];
    for (const attr of node.attributes) {
        const attrName = attr.name.toUpperCase();
        if (attrName !== "STYLE") {
            toRemove.push(attr);
        }
    }
    for (const attributeToRemove of toRemove) {
        node.removeAttributeNode(attributeToRemove);
    }
    // filter styling
    toRemove = [];
    for (const name of node.style) {
        if (!allowedStyling.hasOwnProperty(name)) {
            toRemove.push(name);
        }
        if (name === "background-color" && node.style[name] === "transparent") {
            // google docs adds this unnecessarily
            toRemove.push(name);
        }
    }
    for (let name of toRemove) {
        node.style.removeProperty(name);
    }
};
allowedTagsExtended["SPAN"] = filterExternalSpan;
// add basic tags to extended
Object.assign(allowedTagsExtended, allowedTagsBasic);
// filtering from another field
window.filterInternalNode = function (node) {
    if (node.style) {
        node.style.removeProperty("background-color");
        node.style.removeProperty("font-size");
        node.style.removeProperty("font-family");
    }
    // recurse
    for (const child of node.childNodes) {
        filterInternalNode(child);
    }
};
// filtering from external sources
window.filterNode = function (node, extendedMode) {
    // text node?
    if (node.nodeType === 3) {
        return;
    }
    // descend first, and take a copy of the child nodes as the loop will skip
    // elements due to node modifications otherwise
    const nodes = [];
    for (const child of node.childNodes) {
        nodes.push(child);
    }
    for (const child of nodes) {
        filterNode(child, extendedMode);
    }
    if (node.tagName === "ANKITOP") {
        return;
    }
    let tag;
    if (extendedMode) {
        tag = allowedTagsExtended[node.tagName];
    }
    else {
        tag = allowedTagsBasic[node.tagName];
    }
    if (!tag) {
        if (!node.innerHTML || node.tagName === "TITLE") {
            node.parentNode.removeChild(node);
        }
        else {
            node.outerHTML = node.innerHTML;
        }
    }
    else {
        if (typeof tag === "function") {
            // filtering function provided
            tag(node);
        }
        else {
            // allowed, filter out attributes
            const toRemove = [];
            for (const attr of node.attributes) {
                const attrName = attr.name.toUpperCase();
                if (tag.attrs.indexOf(attrName) === -1) {
                    toRemove.push(attr);
                }
            }
            for (const attributeToRemove of toRemove) {
                node.removeAttributeNode(attributeToRemove);
            }
        }
    }
};
</script>
"""


#span, fld, ctrl, paste is formatted. 
#Capital EFDRC is just for easier code reading. Case doesn't matter.
card_js ="""
<script>
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
    
    window.EFDRCctrldown = function(){
        els = document.querySelectorAll("[data-EFDRC='true']"); 
        for(var e = 0; e < els.length; e++){
            var el = els[e];
            el.setAttribute("contenteditable", "true")
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
        var mimetype = ["text/html", "image/", "video/", "audio/"]
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
                pycmd("EFDRC#paste")
                break;
            }
        }
        
    }

    window.EFDRCaddListeners = function(e, fld, spanBool){
        if(%(paste)s){
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
        
        if(spanBool){
            el.addEventListener('keydown', function(event){
                if (event.keyCode == 8) {
                    event.stopPropagation();
                }
            })
        }

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

        })
    }
    if(%(ctrl)s){
        window.addEventListener('keydown',function(event){
            if(event.keyCode == 17 || event.keyCode == 91){ //91 is cmd key in mac
                EFDRCctrldown();
            }   
        })

        window.addEventListener('keyup',function(event){
            if(event.keyCode == 17 || event.keyCode == 91){
                EFDRCctrlup();
            }    
        })

    }
}

els = document.querySelectorAll("[data-EFDRCfield='%(fld)s']");
for(var e = 0; e < els.length; e++){
    var el = els[e];
    EFDRCaddListeners(el, "%(fld)s", %(span)s);
}

if(!%(ctrl)s){
    for(var e = 0; e < els.length; e++){
        els[e].setAttribute("contenteditable", "true");
    }
}

</script>
"""