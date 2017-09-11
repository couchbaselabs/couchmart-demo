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
            console.log(styleSheet);
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