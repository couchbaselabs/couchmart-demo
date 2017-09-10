$( ".submit-btn" ).click(function() {
  var active_buttons = $(".btn-product.active");
  var orders = [];

  if (active_buttons.length < 5){
      alert("Please select 5 items before submitting");
      return;
  }

  active_buttons.each(function (index){
      orders.push($(this).val())
  });

  $.post( "/submit_order",
      JSON.stringify({
          name: $("#name-box").val(),
          order: orders}),
          function( data ) {
            alert("Order submitted!!")
          });
});