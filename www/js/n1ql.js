var showing_front = false;
window.onload = function N1QLSocket(){
    if ("WebSocket" in window) {
        // Let us open a web socket
        var ws = new WebSocket("ws://" + location.host + "/liveorders");
        ws.onopen = function() {
            // Web Socket is connected, send data using send()
            ws.send("Bingo Bango");
        };

        ws.onmessage = function (evt)
        {

            var msg = JSON.parse(evt.data);
            images=msg['images']
            if (showing_front){
                $("#happy-shopper").text(msg['name']);
                $("#slot1").css({backgroundImage : 'url("' + images[0] + ' ")'});
                $("#slot2").css({backgroundImage : 'url("' + images[1] + ' ")'});
                $("#slot3").css({backgroundImage : 'url("' + images[2] + ' ")'});
                $("#slot4").css({backgroundImage : 'url("' + images[3] + ' ")'});
                $("#slot5").css({backgroundImage : 'url("' + images[4] + ' ")'});
            }
            else
            {
                $("#unhappy-shopper").text(msg['name']);
                $("#backslot1").css({backgroundImage : 'url("' + images[4] + ' ")'});
                $("#backslot2").css({backgroundImage : 'url("' + images[3] + ' ")'});
                $("#backslot3").css({backgroundImage : 'url("' + images[2] + ' ")'});
                $("#backslot4").css({backgroundImage : 'url("' + images[1] + ' ")'});
                $("#backslot5").css({backgroundImage : 'url("' + images[0] + ' ")'});
            }
            //
            $(".order-card").flip(!showing_front);
            showing_front = ! showing_front;
        };

        ws.onclose = function()
        {
            // websocket is closed.
            $("#unhappy-shopper").text("Ready");
            $("#happy-shopper").text("Please place an order");
            setTimeout(function(){N1QLSocket()}, 5000);
        };
    }

    else
    {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
}