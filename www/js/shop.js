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
    $(".search-btn").attr("disabled", true);
    $.get("/search", function (data){
        console.log(data);
        $(".search-btn").attr("disabled", false);
    });
});

$(".type-btn").click(function(){
    if ($(this).hasClass("active")){
        $(".btn-product").each(function () {
              $(this).parent().show();
        });
        return;
    }

    $(".type-btn.active").each(function(){
        $(this).removeClass("active");
    });

    $.get("/filter?type=" + $(this).val(), function (data){
        $(".btn-product").each(function () {
          if (data['keys'].indexOf($(this).val()) === -1){
              $(this).parent().hide();
          }else{
              $(this).parent().show();
          }
        })
    });
});

window.onload = function BackgroundSocket(){

    if ("WebSocket" in window) {
       // Let us open a web socket
       var ws = new WebSocket("ws://localhost:8888/socket");

       ws.onopen = function() {
          // Web Socket is connected, send data using send()
          ws.send("Bingo Bango");
       };

       ws.onmessage = function (evt)
       {
          var msg = JSON.parse(evt.data);
          if (msg['fts']){
              $(".search-container").show();
          } else {
              $(".search-container").hide();
          }

        console.log("received: "+msg)

     };

     ws.onclose = function()
     {
        // websocket is closed.
        alert("Connection is closed...");
     };
    }
    else
    {
       // The browser doesn't support WebSocket
       alert("WebSocket NOT supported by your Browser!");
    }
 };

