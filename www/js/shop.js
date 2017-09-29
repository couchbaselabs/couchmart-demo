$( ".submit-btn" ).click(function() {
    var active_buttons = $(".btn-product.active");
    var name_box = $("#name-box");
    var orders = [];

    if (!name_box.val()){
        alert("Please enter a name before submitting.");
        return;
    }
    if (active_buttons.length < 5){
        alert("Please select 5 items before submitting.");
        return;
    }


    active_buttons.each(function (index){
        orders.push($(this).val())
    });

    $.post( "/submit_order",
        JSON.stringify({
            name: name_box.val(),
            order: orders}),
        function( data ) {
            alert("Order submitted!")
        })
        .fail(function () {
            alert("Error submitting order.")
        });

    active_buttons.removeClass("active");
});

$( ".btn-product" ).click(function (event){
    var active_buttons = $(".btn-product.active");
    if (active_buttons.length >= 5) {
        if (!$(this).hasClass("active")) {

            alert("Cannot select more than 5 items.");
            event.stopPropagation();
        }
    }
});

var clear_filter = function (){
    $(".btn-product").each(function () {
        $(this).parent().show();
    });
};

var clear_types = function (){
    $(".type-btn").each(function () {
        $(this).removeClass("active");
    });
};

function hasTouch() {
    return "ontouchstart" in window || window.navigator.msMaxTouchPoints > 0;
}

if (hasTouch()) { // remove all :hover stylesheets
    try { // prevent exception on browsers not supporting DOM styleSheets properly
        for (var si in document.styleSheets) {
            var styleSheet = document.styleSheets[si];
            if (!styleSheet.rules) continue;

            for (var ri = styleSheet.rules.length - 1; ri >= 0; ri--) {
                if (!styleSheet.rules[ri].selectorText) continue;

                if (styleSheet.rules[ri].selectorText.match(':hover')) {
                    styleSheet.deleteRule(ri);
                }
            }
        }
    } catch (ex) {
    }
}

$(".search-btn").click(function() {
    if($('.search-input').val() === ""){
        clear_types();
        clear_filter();
        return;
    }
    $(".search-btn").attr("disabled", true);
    $("body > div > div > div > div > div.container > div:nth-child(1) > div.col-md-4.col-sm-6.col-8.search-container > button > img").addClass("rotate");
    $.get("/search?q="+$(".search-input").val(), function (data){
        clear_types();
        $(".btn-product").each(function () {
            if (data['keys'].indexOf($(this).val()) === -1){
                $(this).parent().hide();
            }else{
                $(this).parent().show();
            }
        });
    }).fail(function(){
        alert("Error submitting search.")
    }).always(function (){
        $("body > div > div > div > div > div.container > div:nth-child(1) > div.col-md-4.col-sm-6.col-8.search-container > button > img").removeClass("rotate");
        $(".search-btn").attr("disabled", false);
    });
});

$(".type-btn").click(function(){
    $('.search-input').val('');
    if ($(this).hasClass("active")){
        $(".btn-product").each(function () {
            $(this).parent().show();
        });
        return;
    }

    clear_types();

    $.get("/filter?type=" + $(this).val(), function (data){
        $(".btn-product").each(function () {
            if (data['keys'].indexOf($(this).val()) === -1){
                $(this).parent().hide();
            }else{
                $(this).parent().show();
            }
        });
    });
});

$(".type-row").hover(function(){
    $(this).css("border-style", "none");
    $(this).css("-webkit-box-shadow", "none");
    $(this).css("-moz-box-shadow", "none");
    $(this).css("box-shadow", "none");
});

$(".type-row").click(function(){
    $(this).css("border-style", "none");
    $(this).css("-webkit-box-shadow", "none");
    $(this).css("-moz-box-shadow", "none");
    $(this).css("box-shadow", "none");
});

$(".search-container").hover(function(){
    $(this).css("border-style", "none");
    $(this).css("-webkit-box-shadow", "none");
    $(this).css("-moz-box-shadow", "none");
    $(this).css("box-shadow", "none");
});

$(".search-container").click(function(){
    $(this).css("border-style", "none");
    $(this).css("-webkit-box-shadow", "none");
    $(this).css("-moz-box-shadow", "none");
    $(this).css("box-shadow", "none");
});

$(document).ready(function(){
    $('#name-box').keypress(function(e){
        if(e.keyCode==13)
            $('.submit-btn').click();
    });
});

$(document).ready(function(){
    $('.search-input').keypress(function(e){
        if(e.keyCode==13)
            $('.search-btn').click();
    });
});

$(document).ready(function(){
    $('.search-input').on('input', function(e){
        if($('.search-input').val() === ""){
            clear_filter();
            clear_types();
        }
    });
});

window.onload = function ShopSocket(){

    if ("WebSocket" in window) {
        // Let us open a web socket
        var ws = new WebSocket("ws://" + location.host + "/nodestatus");
        ws.onopen = function() {
            console.log("started");
            // Web Socket is connected, send data using send()
            ws.send("Shop Socket Connected");
        };

        ws.onmessage = function (evt)
        {
            var msg = JSON.parse(evt.data);
            if (msg['fts']){
                $(".search-container").show();
            } else {
                $(".search-container").hide();
            }

            if (msg['n1ql']){
                $(".type-row").show();
            } else {
                $(".type-row").hide();
            }
            console.log("received: "+msg)

        };

        ws.onclose = function()
        {
            // websocket is closed.
            setTimeout(function(){ShopSocket()}, 5000);
        };
    }
    else
    {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
};

