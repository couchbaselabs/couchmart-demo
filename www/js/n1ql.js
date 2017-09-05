var showing_front = false;
window.onload = function BackgroundSocket(){
  if ("WebSocket" in window) {
     // Let us open a web socket
     var ws = new WebSocket("ws://localhost:8888/liveorders");
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
        $("#backslot1").css({backgroundImage : 'url("' + images[0] + ' ")'});
        $("#backslot2").css({backgroundImage : 'url("' + images[1] + ' ")'});
        $("#backslot3").css({backgroundImage : 'url("' + images[2] + ' ")'});
        $("#backslot4").css({backgroundImage : 'url("' + images[3] + ' ")'});
        $("#backslot5").css({backgroundImage : 'url("' + images[4] + ' ")'});
      }
      $(".flip").flip(showing_front);
      showing_front = ! showing_front;
      $(".flip").flip({reverse: showing_front});
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
}