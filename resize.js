var preserve_ratio = "%(preserve_ratio)s"; // string
var min_height = %(min_height)d;
var min_width = %(min_width)d;
var resizable_style = "%(resizable_style)s";

function resizeImage(idx, img){
    $resizeImage($(img));
}

async function $resizeImage($img){
    var img = $img[0];
    while (img.naturalWidth == 0 || img.naturalHeight == 0) {
        await new Promise(r => setTimeout(r, 1000));
    }
    var preserve_ratio_in_resizable = false;
    if (preserve_ratio == "current" || preserve_ratio == "original"){
        preserve_ratio_in_resizable = true;
    }
    if ($img.resizable("instance") == undefined ) {
        $maybe_remove_a_dimension($img);
        var minHeight = ((min_height == null) ? 0: min_height)
        var minWidth = ((min_width == null) ? 0: min_width)
        $img.resizable({
            aspectRatio: preserve_ratio_in_resizable,
            minHeight: minHeight,
            minWidth: minWidth
        });
        $img.css("max-width", "100%%"); //%% because a single percent would make a python error during formatting of this file.
        var $divUi = $img.parents("div[class^=ui-]");
        $divUi.attr("contentEditable", "false");
        $divUi.css("display", "inline-block");
    } else {
        console.log("Trying to apply resizable to image already resizable.");
    }
}

function $cleanResize($field){
    // clean everything related to resize, so that it can be saved and
    // displayed properly in reviewer
    var $divUi = $field.find("div[class^=ui-]");
    $divUi.replaceWith(
        function() {
            return $(this).contents();
        }
    );
    $field.find("img").each(partialCleanResize);
}

function partialCleanResize(idx, img){
    $partialCleanResize($(img));
}

function $partialCleanResize($img){
    // Clean the style in the image. So that max height can be applied again correctly.
    $img.removeClass();
    ["position", "max-width", "max-height", "margin", "resize", "position", "zoom", "display", "top", "left"].forEach(style => {$img.css(style, "");});
    $maybe_remove_a_dimension($img);
}

function $maybe_remove_a_dimension($img){
    if (preserve_ratio == "original"){
        $img.css("width", "");
    }
}

