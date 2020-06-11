(function(){

    var FLD = "%(fld)s"; //string

    els = document.querySelectorAll("[data-EFDRCfield='"+ FLD +"']");
    for(var e = 0; e < els.length; e++){
        var el = els[e];
        EFDRC.addListeners(el, FLD);
        if(EFDRC.CTRL){
            EFDRC.placeholder(el)
        }
    }

    if(!EFDRC.CTRL){
        for(var e = 0; e < els.length; e++){
            els[e].setAttribute("contenteditable", "true");
        }
    }

})()