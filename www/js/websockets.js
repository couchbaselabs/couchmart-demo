window.onload = function NodeStatusSocket(){
    if ("WebSocket" in window) {
       // Let us open a web socket
       var ws = new WebSocket("ws://localhost:8888/nodestatus");

       ws.onopen = function() {
          // Web Socket is connected, send data using send()
          ws.send("Node Status Connected");
       };

       ws.onmessage = function (evt) 
       { 
          var msg = JSON.parse(evt.data);
          LIVE_PARTICLES = msg['nodes'][0]['ops'] + msg['nodes'][1]['ops'] + msg['nodes'][2]['ops'];
          if (msg['nodes'][2]['status'] == "down"){
            $("#node3").css({"background-color" : "rgba(179,108,219,0.25)"});
            NODE_3_ALIVE=false;
          }
          else if (msg['nodes'][2]['status'] == "failed"){
            NODE_3_ALIVE=true;
          }
           else if (msg['nodes'][2]['status'] == "ok"){
            NODE_3_ALIVE=true;
            $("#node3").css({"background-color" : "rgba(179,108,219,1)"});
          }
     };
        
     ws.onclose = function()
     {  
        LIVE_PARTICLES = 0;
        $("#node1").css({"background-color" : "rgba(235,73,113,0.25)"});
        $("#node2").css({"background-color" : "rgba(0,185,190,0.25)"});
        $("#node3").css({"background-color" : "rgba(179,108,219,0.25)"});
        $("#node4").css({"background-color" : "rgba(0,116,224,0.25)"});
        // Try to reconnect in 5 seconds
        setTimeout(function(){NodeStatusSocket()}, 5000);

     };
    }
    else
    {
       // The browser doesn't support WebSocket
       alert("WebSocket NOT supported by your Browser!");
    }
 }