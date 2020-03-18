var preserve_ratio = "%(preserve_ratio)s";
var priorImgs = [];

function savePriorImg(img) {
    var id = priorImgs.length;
    img.setAttribute("data-EFDRCImgId", id);
    priorImgs.push(img.cloneNode());
}

function restorePriorImg(img) {
    /* 
    only save changes to width and height
    resizable img is guranteed to have the data-EFDRCImgId attribute.
    if img was added during review, resizable isn't applied to it. 
    */
    var width = img.style.width;
    var height = img.style.height;

    //apply stored style
    var id = img.getAttribute("data-EFDRCImgId");
    var priorImg = priorImgs[id];
    priorImg.style.width = width;
    priorImg.style.height = height;

    img.parentNode.replaceChild(priorImg, img);

}

async function resizeImage(idx, img) {

    while (!img.complete) {
        //wait for image to load
        await new Promise(r => setTimeout(r, 20));
    }

    savePriorImg(img);

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
        var $divUi = $img.parents("div[class=ui-wrapper]");
        $divUi.attr("contentEditable", "false");
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
    for (var x = 0; x < resizables.length; x++) {
        $(resizables[x]).resizable("destroy");
    }
    var imgs = field.querySelectorAll("[data-EFDRCImgId]");
    for (var x = 0; x < imgs.length; x++) {
        restorePriorImg(imgs[x]);
    }
    priorImgs = [];
}

