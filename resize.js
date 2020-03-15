var preserve_ratio = "%(preserve_ratio)s"; // string
var resizable_style = "%(resizable_style)s";

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

function $cleanResize($field) {
    // clean everything related to resize, so that it can be saved and
    // displayed properly in reviewer
    var $divUi = $field.find("div[class^=ui-]");
    $divUi.replaceWith(
        function () {
            return $(this).contents();
        }
    );
    $field.find("img").each(partialCleanResize);
}

function partialCleanResize(idx, img) {
    // Clean the style in the image. So that max height can be applied again correctly.
    $(img).removeClass();
    ["position", "max-width", "max-height", "margin", "resize", "position", "zoom", "display", "top", "left"].forEach(style => { $(img).css(style, ""); });
}
