window.addEventListener('keydown',function(event){
    if(["ControlLeft", "MetaLeft"].includes(event.code)){
        EFDRC.ctrldown();
    }
})

window.addEventListener('keyup',function(event){
    if(["ControlLeft", "MetaLeft"].includes(event.code)){
        EFDRC.ctrlup();
    }
})
