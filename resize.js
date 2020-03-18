var preserve_ratio = "%(preserve_ratio)s";
var priorAttr = []

function savePriorAttr(img){
    var id = priorAttr.length;
    var storedStyle = {};
    var styleMap = img.attributeStyleMap;
    for(var [par, val] of styleMap.entries()){
        if(par != "width" && par != "height"){
            storedStyle[par] = img.attributeStyleMap.get(par);
        }
    }
    img.setAttribute("data-EFDRCImgId", id);
    priorAttr.push(storedStyle);
}

function restorePriorAttr(img){
    // resizable img is guranteed to have the data-EFDRCImgId attribute.
    // if img wasadded during review, resizable isn't applied to it.

    //remove existing styles
    var styleMap = img.attributeStyleMap;
    for(var [par, val] of styleMap.entries()){
        if(par != "width" && par != "height"){
            img.attributeStyleMap.delete(par);
        }
    }

    //apply stored style
    var id = img.getAttribute("data-EFDRCImgId");
    var savedStyleMap = priorAttr[id];
    for(var par in savedStyleMap){
        img.attributeStyleMap.set(par, savedStyleMap[par]);
    }
    img.removeAttribute("data-EFDRCImgId")
    priorAttr[id] = null;
}

async function resizeImage(idx, img) {

    while (!img.complete) {
        //wait for image to load
        await new Promise(r => setTimeout(r, 20));
    }

    savePriorAttr(img)

    var $img = $(img);
    if ($img.resizable("instance") == undefined) {
        $img.resizable({
            start: function (event, ui) {
                //passing maxWidth to resizable doesn't work because
                //it only takes in pixel values
                ui.element.css("max-width", window.getComputedStyle(img).maxWidth);
                ui.element.css("max-height", window.getComputedStyle(img).maxHeight);

                if (preserve_ratio && event.originalEvent.target.classList.contains("ui-resizable-se")) {
                    //preserve ratio when using corner point to resize
                    $img.resizable("option", "aspectRatio", true).data('ui-resizable')._aspectRatio = true;
                }
            },
            stop: function (event, ui) {
                $img.resizable("option", "aspectRatio", false).data('ui-resizable')._aspectRatio = false;
            },
            classes: {
                //remove unneeded classes
                "ui-resizable-se": ""
            },
            //TODO: if user set minHeight is bigger than 15px,
            //there may be bugs
            minHeight: 15,
            minWidth: 15
        });

        $img.dblclick(onDblClick);
        var $divUi = $img.parents("div[class=ui-resizable]");
        $divUi.attr("contentEditable", "false");
        $divUi.attr("readonly", "true");
        $divUi.css("display", "inline-block");
    } else {
        console.log("Trying to apply resizable to image already resizable.");
    }
}

function onDblClick() {
    var img = this;
    var $img = $(img);
    $img.css("width", "");
    $img.css("height", "");
    var $parents = $img.parents("div[class^=ui-]");
    $parents.css("width", "");
    $parents.css("height", "");
}

function cleanResize(field) {
    var resizables = field.querySelectorAll(".ui-resizable");
    for(var x = 0; x < resizables.length; x++){
        $(resizables[x]).resizable("destroy");
    }
    var imgs = field.querySelectorAll("[data-EFDRCImgId]")
    for(var x = 0; x < imgs.length; x++){
        restorePriorAttr(imgs[x]);
    }
    priorAttr = [];
}

