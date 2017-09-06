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
          LIVE_PARTICLES = msg['nodes'][0]['ops'] + msg['nodes'][1]['ops'] + msg['nodes'][2]['ops'];
          if (msg['nodes'][2]['status'] == "broken"){
            $("#node3").css({"background-color" : "red"});
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
 }