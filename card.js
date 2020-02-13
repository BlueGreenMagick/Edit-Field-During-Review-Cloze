(function(){

    var FLD = "%(fld)s"; //string
    var CTRL = %(ctrl)s; //bool

    els = document.querySelectorAll("[data-EFDRCfield='"+ FLD +"']");
    for(var e = 0; e < els.length; e++){
        var el = els[e];
        window.EFDRCaddListeners(el, FLD);
    }

    if(!CTRL){
        for(var e = 0; e < els.length; e++){
            els[e].setAttribute("contenteditable", "true");
        }
    }
    
})()