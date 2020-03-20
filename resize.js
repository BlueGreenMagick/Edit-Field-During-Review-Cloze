EFDRC.preserve_ratio = parseInt("%(preserve_ratio)d");
EFDRC.DEFAULTRESIZE = "%(resize_state)s";
EFDRC.resizeImageMode = EFDRC.DEFAULTRESIZE;
EFDRC.priorImgs = [];

EFDRC.savePriorImg = function (img) {
    var id = EFDRC.priorImgs.length;
    EFDRC.priorImgs.push(img.cloneNode());
    img.setAttribute("data-EFDRCImgId", id);
}

EFDRC.restorePriorImg = function (img) {
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

EFDRC.ratioShouldBePreserved = function (event) {
    if (EFDRC.preserve_ratio == 1 && event.originalEvent.target.classList.contains("ui-resizable-se")) {
        return true;
    } else if (EFDRC.preserve_ratio == 2) {
        return true;
    } else {
        return false;
    }
}

EFDRC.maybeRemoveHeight = function (img) {
    $img = $(img)
    if (!img.naturalHeight) { return; }
    var originalRatio = img.naturalWidth / img.naturalHeight;
    var currentRatio = $img.width() / $img.height();
    if (Math.abs(originalRatio - currentRatio) < 0.01) {
        $img.css("height", "");
    }
}

EFDRC.resizeImage = async function (idx, img) {

    while (!img.complete) {
        //wait for image to load
        await new Promise(r => setTimeout(r, 20));
    }

    EFDRC.savePriorImg(img);

    var $img = $(img);
    if ($img.resizable("instance") == undefined) { // just in case?
        var aspRatio = (EFDRC.preserve_ratio == 2);
        $img.resizable({
            start: function (event, ui) {
                //passing maxWidth to resizable doesn't work because
                //it only takes in pixel values
                computedStyle = window.getComputedStyle(img);
                ui.element.css("max-width", computedStyle.maxWidth);
                ui.element.css("max-height", computedStyle.maxHeight);
                $img.css("max-width", "100%%"); // escape percentage because string formatter
                $img.css("max-height", "100%%");
                if (parseFloat(computedStyle.minWidth)) { // not 0
                    ui.element.css("min-width", computedStyle.minWidth);
                }
                if (parseFloat(computedStyle.minHeight)) {
                    ui.element.css("min-height", computedStyle.minHeight);
                }
                if (EFDRC.ratioShouldBePreserved(event)) {
                    //preserve ratio when using corner point to resize
                    $img.resizable("option", "aspectRatio", true).data('ui-resizable')._aspectRatio = true;
                }
            },
            stop: function (event, ui) {
                $img.resizable("option", "aspectRatio", false).data('ui-resizable')._aspectRatio = false;
                EFDRC.maybeRemoveHeight(img, $img, ui); // this might not be working
            },
            resize: function (event, ui) {
                //I'm not sure if this is working, but too tired to care
                if (EFDRC.ratioShouldBePreserved(event)) {
                    EFDRC.maybeRemoveHeight(img, $img, ui);
                }
            },
            classes: {
                //remove unneeded classes
                "ui-resizable-se": ""
            },
            minHeight: 15,
            minWidth: 15,
            aspectRatio: aspRatio
        });

        $img.dblclick(EFDRC.onDblClick);
        var $divUi = $img.parents("div[class=ui-wrapper]");
        $divUi.attr("contentEditable", "false");
        $divUi.css("display", "inline-block");
    }
}

EFDRC.onDblClick = function () {
    var img = this;
    var $img = $(img);
    $img.css("width", "");
    $img.css("height", "");
    var $parents = $img.parents("div[class^=ui-]");
    $parents.css("width", "");
    $parents.css("height", "");
}

EFDRC.cleanResize = function (field) {
    var resizables = field.querySelectorAll(".ui-resizable");
    for (var x = 0; x < resizables.length; x++) {
        $(resizables[x]).resizable("destroy");
    }
    var imgs = field.querySelectorAll("[data-EFDRCImgId]");
    for (var x = 0; x < imgs.length; x++) {
        EFDRC.maybeRemoveHeight(imgs[x])
        EFDRC.restorePriorImg(imgs[x]);
    }
    EFDRC.priorImgs = [];
}

EFDRC.maybeResizeOrClean = function (focus) {
    if (focus) {
        // Called from __init__.py on field focus. Else undefined.
        EFDRC.resizeImageMode = EFDRC.DEFAULTRESIZE;
    }
    if (EFDRC.resizeImageMode) {
        $(document.activeElement).find("img").each(EFDRC.resizeImage);
    } else {
        EFDRC.cleanResize(document.activeElement);
    }
}
