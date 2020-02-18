CTRL = "%(ctrl)s";

if(typeof EFDRConctrlkey != "function" && CTRL){
    window.EFDRConctrlkey = function(){
        window.addEventListener('keydown',function(event){
            if(event.code == "ControlLeft"){
                pycmd("EFDRC!ctrldown");
            }    
        })

        window.addEventListener('keyup',function(event){
            if(event.code == "ControlLeft"){
                pycmd("EFDRC!ctrlup");
            }    
        })        
    }
    EFDRConctrlkey()
}