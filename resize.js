EFDRC.preserve_ratio = "%(preserve_ratio)s";
EFDRC.resizeImageMode = "%(resize_state)s";
EFDRC.priorImgs = [];

EFDRC.savePriorImg = function(img) {
    var id = EFDRC.priorImgs.length;
    EFDRC.priorImgs.push(img.cloneNode());
    img.setAttribute("data-EFDRCImgId", id);
}

EFDRC.restorePriorImg = function(img) {
    /* 
    only save changes to width and height
    resizable img is guranteed to have the data-EFDRCImgId attribute.
    if img was added during review, resizable isn't applied to it. 
    */
    var width = img.style.width;
    var height = img.style.height;

    //apply stored style
    var id = img.getAttribute("data-EFDRCImgId");
    var priorImg = EFDRC.priorImgs[id];
    priorImg.style.width = width;
    priorImg.style.height = height;

    img.parentNode.replaceChild(priorImg, img);

}

EFDRC.resizeImage = async function(idx, img) {

    while (!img.complete) {
        //wait for image to load
        await new Promise(r => setTimeout(r, 20));
    }

    EFDRC.savePriorImg(img);

    var $img = $(img);
    if ($img.resizable("instance") == undefined) {
        $img.resizable({
            start: function (event, ui) {
                //passing maxWidth to resizable doesn't work because
                //it only takes in pixel values
                computedStyle = window.getComputedStyle(img);
                ui.element.css("max-width", computedStyle.maxWidth);
                ui.element.css("max-height", computedStyle.maxHeight);
                if(parseFloat(computedStyle.minWidth)){ // not 0
                    ui.element.css("min-width", computedStyle.minWidth);
                }
                if(parseFloat(computedStyle.minHeight)){ 
                    ui.element.css("min-height", computedStyle.minHeight);
                }
                if (EFDRC.preserve_ratio && event.originalEvent.target.classList.contains("ui-resizable-se")) {
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

        $img.dblclick(EFDRC.onDblClick);
        var $divUi = $img.parents("div[class=ui-wrapper]");
        $divUi.attr("contentEditable", "false");
        $divUi.css("display", "inline-block");
    } else {
        console.log("Trying to apply resizable to image already resizable.");
    }
}

EFDRC.onDblClick = function() {
    var img = this;
    var $img = $(img);
    $img.css("width", "");
    $img.css("height", "");
    var $parents = $img.parents("div[class^=ui-]");
    $parents.css("width", "");
    $parents.css("height", "");
}

EFDRC.cleanResize = function(field) {
    var resizables = field.querySelectorAll(".ui-resizable");
    for (var x = 0; x < resizables.length; x++) {
        $(resizables[x]).resizable("destroy");
    }
    var imgs = field.querySelectorAll("[data-EFDRCImgId]");
    console.log(imgs)
    for (var x = 0; x < imgs.length; x++) {
        EFDRC.restorePriorImg(imgs[x]);
    }
    EFDRC.priorImgs = [];
}

EFDRC.maybeResizeOrClean = function(){
    if(EFDRC.resizeImageMode){
        $(document.activeElement).find("img").each(EFDRC.resizeImage);
    }else{
        EFDRC.cleanResize(document.activeElement);
    }
}
