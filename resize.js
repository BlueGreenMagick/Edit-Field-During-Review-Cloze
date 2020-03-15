var preserve_ratio = "%(preserve_ratio)s"; // string
var resizable_style = "%(resizable_style)s";

function resizeImage(idx, img){
    $resizeImage($(img));
}

async function $resizeImage($img){
    var img = $img[0];
    while (img.naturalWidth == 0 || img.naturalHeight == 0) {
        await new Promise(r => setTimeout(r, 1000));
    }
    if ($img.resizable("instance") == undefined ) {
        var minHeight = 15;
        var minWidth = 15;
        if(preserve_ratio){
            $img.resizable({
                start: function(event, ui){
                    if(event.originalEvent.target.classList.contains("ui-resizable-se")){
                        $img.resizable( "option", "aspectRatio", true ).data('ui-resizable')._aspectRatio = true;
                    }
                },
                stop: function(event, ui){
                    $img.resizable( "option", "aspectRatio", false ).data('ui-resizable')._aspectRatio = false;
                },
                minHeight: minHeight,
                minWidth: minWidth
            });
        }else{
            $img.resizable({
                aspectRatio: preserve_ratio,
                minHeight: minHeight,
                minWidth: minWidth
            });
        }
        $img.css("max-width", "100%%"); //%% because a single percent would make a python error during formatting of this file.
        $img.dblclick(onDblClick);
        var $divUi = $img.parents("div[class^=ui-]");
        $divUi.attr("contentEditable", "false");
        $divUi.css("display", "inline-block");
    } else {
        console.log("Trying to apply resizable to image already resizable.");
    }
}

function onDblClick(){
    var img = this;
    var $img = $(img);
    $img.css("width", "");
    $img.css("height", "");
    var $parents = $img.parents("div[class^=ui-]");
    $parents.css("width", "");
    $parents.css("height", "");
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


