/*
    If focus in on bottom.web, ctrl key press is not catched by global_card.js
    So this code catches ctrl key presses when focus in on bottom.web
*/

CTRL = "%(ctrl)s";

if(typeof EFDRConctrlkey != "function" && CTRL){
    window.EFDRConctrlkey = function(){
        window.addEventListener('keydown',function(event){
            if(["ControlLeft", "MetaLeft"].includes(event.code)){
                pycmd("EFDRC!ctrldown");
            }    
        })

        window.addEventListener('keyup',function(event){
            if(["ControlLeft", "MetaLeft"].includes(event.code)){
                pycmd("EFDRC!ctrlup");
            }    
        })        
    }
    EFDRConctrlkey()
}