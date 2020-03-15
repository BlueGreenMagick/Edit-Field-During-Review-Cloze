var preserve_ratio = "%(preserve_ratio)s";

async function resizeImage(idx, img) {

    while (img.naturalWidth == 0 || img.naturalHeight == 0) {
        //wait for image to load
        await new Promise(r => setTimeout(r, 1000));
    }

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
            minHeight: 15,
            minWidth: 15
        });

        $img.dblclick(onDblClick);
        var $divUi = $img.parents("div[class^=ui-]");
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
    resizables = field.querySelectorAll(".ui-resizable");
    for(var x = 0; x < resizables.length; x++){
        $(resizables[x]).resizable("destroy");
    }
}