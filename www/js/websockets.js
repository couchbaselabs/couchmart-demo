function setAlpha(node_elem, new_alpha){
  var bg = $(node_elem).css('backgroundColor');
  var rgb_array = bg.slice(4).split(',');
  var newBg = 'rgba('+rgb_array[0]+','+parseInt(rgb_array[1])+','+parseInt(rgb_array[2])+','+new_alpha+')';
  $(node_elem).css('backgroundColor',newBg);
}

window.onload = function NodeStatusSocket(){

    $(".azure").hide();

    if ("WebSocket" in window) {
       // Let us open a web socket
       var ws = new WebSocket("ws://" + location.host + "/nodestatus");

       ws.onopen = function() {
          // Web Socket is connected, send data using send()
          ws.send("Node Status Connected");
       };

       ws.onmessage = function (evt) 
       { 
          var msg = JSON.parse(evt.data);
          total_ops = 0;
          for (i = 0; i < msg['nodes'].length; i++){
            node = msg['nodes'][i];
            node_elem = "#node" + (i+1);
            if (node['status'] == "down"){
              $(node_elem).hide();
            }
            else if (node['status'] == "failed"){
              setAlpha(node_elem,0.25);
              $(node_elem).show();
            }
            else {
              setAlpha(node_elem,1);
              $(node_elem).show();
            }
            total_ops += node['ops'];
          }
          LIVE_PARTICLES = total_ops;
          if (msg['xdcr']){
             $('.azure').show();
          }
          else{
             $('.azure').hide();
          }
     };
        
     ws.onclose = function()
     {  
        LIVE_PARTICLES = 0;
        for (i= 0; i < 5; i++){
           node_elem = "#node" + (i+1);
           setAlpha(node_elem,0.25);
        }
        $(".azure").hide();

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