// Global date variable for today's date

var d = new Date();
var date = d.getFullYear() + "-" + (d.getMonth()+1) + "-" + d.getDate();

// Date settings for Semantic UI

$(document).ready(function(){
    var calendarOpts = {
        type: 'date',
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                var day = date.getDate() + '';
                if (day.length < 2) {
                    day = '0' + day;
                }
                var month = (date.getMonth() + 1) + '';
                if (month.length < 2) {
                    month = '0' + month;
                }
                var year = date.getFullYear();
                return year + '-' + month + '-' + day;
            }
        }
    };
    $('.ui.calendar').calendar(calendarOpts);
});

// Request Booking

function request_booking (event) {
    event.preventDefault();

    intender = $('input[name="intender"]').val();
    category = $('input[name="visitor-category"]').val();
    csrfmiddlewaretoken = $('input[name="csrf"]').val();
    booking_from = $('input[name="request-booking-from"]').val();
    booking_to = $('input[name="request-booking-to"]').val();
    number_of_people = $('input[name="number-of-people"]').val();
    number_of_rooms = $('input[name="number-of-rooms"]').val();
    purpose_of_visit = $('input[name="purpose-of-visit"]').val();

    if (new Date(booking_from) < new Date(date)) {
        alertModal ('Oops! Those dates are not available for booking.');
        return;
    }

    if (new Date(booking_from) >= new Date(booking_to)) {
        alertModal ('Please check start date and end date!');
        return;
    }

    if (number_of_people < 1) {
        alertModal ("Oops! People can't be zero or negative in number.");
        return;
    }

    if (number_of_rooms < 1) {
        alertModal ("Oops! Number of rooms can't be zero or negative.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/request-booking/',
        data: {
            'intender' : intender,
            'category' : category,
            'csrfmiddlewaretoken': csrfmiddlewaretoken,
            'booking_from' : booking_from,
            'booking_to' : booking_to,
            'number-of-people' : number_of_people,
            'purpose-of-visit' : purpose_of_visit,
            'number-of-rooms' : number_of_rooms,
        },
        success: function(data) {
            alertModal(" Congratulations! Your booking has been placed successfully\n Please wait for confirmation");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Meal Record

$('.bookameal-submit').click(function(event){
    event.preventDefault();
    var pk = $(this).attr('data-pk');
    var food = []
    $('input[name=food'+pk+']:checked').each(function(){
        food.push($(this).val());
    });
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/record-meal/',
        data: {
            'pk' : pk,
            'booking' : $('input[name="meal-booking-id"]').val(),
            'numberofpeople': $('input[name="numberofpeople-meal"]').val(),
            'food':food,
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        },
        success: function(data) {
            alertModal('Great! Meals recorded successfully');
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
});

// Update Inventory

function update_inventory_form(id){
    $('#show-'.concat(id)).fadeToggle();
    $('#select-'.concat(id)).fadeToggle();
    $('#submit-'.concat(id)).fadeToggle();
};

// Something Inventory

function submit_inventory_form(id){
    id = id;
    quantity = $('#input-'.concat(id))[0].value;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/update-inventory/',
        data: {
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'id' : id,
            'quantity' : quantity,
        },
        success: function(data) {
            $('#show-'.concat(id))[0].innerHTML = quantity;
            console.log(room_status);
            $('#show-'.concat(id)).fadeToggle();
            $('#select-'.concat(id)).fadeToggle();
            $('#submit-'.concat(id)).fadeToggle();
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

$('#add-more-items-inventory').click(function(event){

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/add-to-inventory/',
        data: {
            'item' : $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value,
            'quantity' : $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value,
            'amount' : $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value,
            'consumable' : $('.reset-this-form')[0].children[2].children[3].children[1].children[0].value,
            'csrfmiddlewaretoken': '{{csrf_token}}'
        },
        success: function(data) {
            $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value = "";
            $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value = "";
            $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value = "";
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });

});

$('#add-item-form-submit').click(function(event){
    event.preventDefault();
    if($('input[name="consumable"]:checked')){
        consumable = 'True';
    }
    else{
        consumable = 'False';
    }
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/add-to-inventory/',
        data: {
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'item_name' : $('input[name="item-name"]').val(),
            'quantity' : $('input[name="quantity_add"]').val(),
            'cost' : $('input[name="cost"]').val(),
            'consumable' : consumable,
            'bill_number' : $('input[name="bill_number"]').val()
        },
        success: function(data) {
            $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value = "";
            $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value = "";
            $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value = "";
        },
        error: function(xhr, data, err) {
            alertModal('Something missing! Please refill the form');
        }

    });

});

// Edit Room Status

function edit_room_status(id){
    $('#show-'.concat(id)).fadeToggle();
    $('#select-'.concat(id)).fadeToggle();
    $('#submit-'.concat(id)).fadeToggle();
};

var room_status;

function submit_room_status(id){
    room_number = id;
    room_status = $('#input-'.concat(id))[0].value;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/edit-room-status/',
        data: {
            'csrfmiddlewaretoken': '{{csrf_token}}',
            'room_number' : room_number,
            'room_status' : room_status,
        },
        success: function(data) {
            $('#show-'.concat(id))[0].innerHTML = room_status;
            console.log(room_status);
            $('#show-'.concat(id)).fadeToggle();
            $('#select-'.concat(id)).fadeToggle();
            $('#submit-'.concat(id)).fadeToggle();
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Confirm Booking

function confirm_booking (id) {

    csrfmiddlewaretoken = $('input[name=csrf]').val();
    category = $('input[name=category-'+id+']').val();
    rooms = $('select[name=alloted-rooms-'+id+']').val();

    if (category == 0) {
        alertModal("Please fill the category to confirm.");
        return;
    }

    if (rooms == 0) {
        alertModal("Please fill the rooms to confirm booking.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/confirm-booking/',
        data: {
            'booking-id' : id,
            'csrfmiddlewaretoken': csrfmiddlewaretoken,
            'category' : category,
            'rooms' : rooms,
        },
        success: function(data) {
            alertModal("This booking has been confirmed");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Reject Booking

function reject_booking (id) {

    remarks = $('input[name=cancellation-remarks-'+id+']').val();
    if (remarks == '') {
        alertModal("Please fill in why you want to reject this booking in remarks.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/reject-booking/',
        data: {
            'booking-id' : $('input[name=booking-id-'+id+']').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'remark' : remarks,
        },
        success: function(data) {
            alertModal("This booking has been rejected");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Cancel Booking

function cancel_booking (id) {

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/cancel-booking/',
        data: {
            'booking-id' : $('input[name=booking-id-'+id+']').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'charges' : $('input[name=charges-'+id+']').val(),
        },
        success: function(data) {
            alertModal("This booking has been cancelled.");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Forward Booking

function forward_booking (id) {
    id=id;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/forward-booking/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'id' : id,
        },
        success: function(data) {
            alertModal("This booking has been forwarded");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
}

// Cancel Active Booking

function cancel_active_booking (id, booking_from) {

    if (new Date(date) <= new Date(booking_from)){
        alertModal('Cannot cancel as booking start date has arrived!');
    }


    $.ajax({
        type: 'POST',
        url: '/visitorhostel/cancel-booking-request/',
        data: {
            'booking-id' : id,
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        },
        success: function(data) {
            alertModal("Your cancellation request has been placed.\n Please await confirmation.");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Edit Inventory

$("#edit-inventory").click(function(e){
    $(".inventory-item").slideToggle();
    $(".inventory-form").slideToggle();
    $("#update-inventory-submit").slideToggle();
});
$("#update-inventory-submit").click(function(e){
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/bookaroom/',
        data: {
            'csrfmiddlewaretoken' : '{{csrf_token}}',
            'data' : data
        },
        success: function(data) {
            alertModal("Congratulations! Inventory is updated successfully");
        },
        error: function(data, err) {
            alertModal('Something missing! PLease refill the form');
        }
    });
});

// Submit Visitor Details

function submit_visitor_details (id) {
    vis_length = $('input[name=length-'+id+']').val();
    var temp = parseInt(vis_length);
    for (var i=1; i<=vis_length+1; i++) {
        csrfmiddlewaretoken = $('input[name="csrf"]').val();
        name = $('input[name=visitor-name-'+id+'-'+i+']').val();
        phone = $('input[name=phone-'+id+'-'+i+']').val();
        email = $('input[name=email-'+id+'-'+i+']').val();
        address = $('input[name=address-'+id+'-'+i+']').val();

        if (name == '') {
            alertModal("You didn't fill a visitor name! Please refill the form.");
            return;
        }

        if (phone == '') {
            alertModal("You didn't fill a visitor's phone number. Please fill the form again.");
            return;
        }
    }

    for (var j=1; j<=temp+1; j++) {
        csrfmiddlewaretoken = $('input[name="csrf"]').val();
        name = $('input[name=visitor-name-'+id+'-'+j+']').val();
        phone = $('input[name=phone-'+id+'-'+j+']').val();
        email = $('input[name=email-'+id+'-'+j+']').val();
        address = $('input[name=address-'+id+'-'+j+']').val();

        $.ajax({
            type: 'POST',
            url: '/visitorhostel/check-in/',
            data: {
                'booking-id' : id,
                'csrfmiddlewaretoken' : csrfmiddlewaretoken,
                'name' : name,
                'phone' : phone,
                'email' : email,
                'address' : address
            },
            success: function(data) {
                alertModal("Great! Visitor's details have been recorded successfully");
            },
            error: function(data, err) {
                alertModal('Something missing! Please refill the form');
            }
        });
    }
    setTimeout(function() {
        window.location.replace('http://localhost:8000/visitorhostel');
    }, 1500);
}

// Check Out

function check_out (id , mess_bill , room_bill) {
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/check-out/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'id' : id,
            'mess_bill' : mess_bill,
            'room_bill' : room_bill,
        },
        success: function(data) {
            alertModal("Visitor has Checked Out ");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/visitorhostel');
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
}

function find_available_rooms () {
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/room-availability/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'start_date' : $('input[name=start-date]').val(),
            'end_date' : $('input[name=end-date]').val(),

        },
        success: function(data) {
            $('#replace-this-div').html(data);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
}


// Various Modals

function modalAddItem(){
    $('#addItemModal').modal('show');
}

function bookingRequestModal(id){
    $('#booking-request-'.concat(id)).modal('show');
}

function cancellationRequestModal(id) {
    $('#cancellation-request-'.concat(id)).modal('show');
}

function bookingDetailsModal(id){
    $('#booking-details-'.concat(id)).modal('show');
}

function checkInModal (id, booking_from) {
    if (new Date(booking_from) > new Date(date)) {
        alertModal ('Cannot check in as booking start date yet not reached.');
        return;
    }
    $('#check-in-modal-'.concat(id)).modal('show');
}

function checkOutModal(id) {
    $('#check-out-modal-'.concat(id)).modal('show');
}

function alertModal(alert) {
    $('#append-alert').html(alert);
    $('#alert-modal').modal('show');
}

function requestModal() {
    $('#requestModal').modal('show');
}

// Information Tooltip on Categories

$('.info.circle.icon')
  .popup({
    inline: true
  })
;

