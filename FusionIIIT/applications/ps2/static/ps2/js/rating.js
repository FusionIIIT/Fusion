/*!
 * # Semantic UI 2.2.12 - Rating
 * http://github.com/semantic-org/semantic-ui/
 *
 *
 * Released under the MIT license
 * http://opensource.org/licenses/MIT
 *
 */

$(document).ready(function(){
  console.log("TTTTTTTT");
});

function addtoinv(event) {  
   var department = $('input[name="Department"]');
   var name = $('input[name="name"]').val();
   var date = $('input[name="date"]');
   var price = $('input[name="price"]').val();   
   var quantity = $('input[name="quantity"]').val();

    if (name == "a")
    {
      alert("The Inventory can't be updated successfully");
      return;
    }
   else
   {
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '.',
        data: {
            'department' : department,
            'name' : name,
            'date' : date,
            'price' : price,
            'quantity' : quantity,            
        },
        success: function(data) {
            alert("The Inventory has been updated successfully");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/ps2');
            }, 1500);
        },
    });
  }
};