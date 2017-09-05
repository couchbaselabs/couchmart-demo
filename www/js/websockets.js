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
//                  document.body.style.background = received_msg;
      console.log("received: "+msg)
      for (var key in msg) {
        if (msg.hasOwnProperty(key)) {
          console.log(key + " -> " + msg[key]);
          var c = document.getElementById(key);
          var ctx = c.getContext("2d");
          ctx.fillStyle=msg[key];
          ctx.fillRect(20,20,160,60);
        }
      }
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