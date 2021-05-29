var myLib = (function(){
   'use strict'; 
    var lib = {};

    lib.loadMore = function(){
        var xhr = new XMLHttpRequest();
        var method = 'GET';
        var url = '/ajax/load_snapshots'; 
        
        xhr.addEventListener('load',lib.displayLoadedImages); 
        xhr.addEventListener('error',lib.displayXhrError); 

        xhr.open(method, url, true);
        xhr.send();
    }
    
    lib.displayLoadedImages = function(e){
        lib.removeLoadButton();
        lib.appendImages(e.target.responseText);
    }


    lib.displayXhrError = function(){
        
    }

    lib.removeLoadButton = function(){
        document.getElementById('snapshots-loader-wrapper').remove();
    }
    
    lib.appendImages = function(html){
        document.getElementById('snapshots-container').innerHTML += html;
        lib.setLoadListener();
    }
    
    lib.setLoadListener = function(){
        var loadButton = document.getElementById('load-more-button');
        if(loadButton !== null){
            loadButton.addEventListener('click', lib.loadMore);
        }
    }

    //TODO flask sessions instead of messing w/ javascript

    return lib

}());

document.addEventListener('DOMContentLoaded', function(e){
    myLib.setLoadListener();
});
