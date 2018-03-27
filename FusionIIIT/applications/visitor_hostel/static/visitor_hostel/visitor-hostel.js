// Request Booking

$('#request-booking-form-submit').on('click', function(event){
    event.preventDefault();

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

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/request-booking/',
        data: {
            'intender' : $('input[name="intender"]').val(),
            'category' : $('input[name="visitor-category"]').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'booking_from' : $('input[name="request-booking-from"]').val(),
            'booking_to' : $('input[name="request-booking-to"]').val(),
            'number-of-people' : $('input[name="number-of-people"]').val(),
            'purpose-of-visit' : $('input[name="purpose-of-visit"]').val(),
        },
        success: function(data) {
            alert("Success");
            $('#request-booking-form')[0].reset();
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
});

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
            alert('Success');
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
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
            alert('Something missing! PLease refill the form');
        }
    });
};


$('.plus').click(function(event){
    event.preventDefault();
    if($('#add-item-section')[0].style.display == 'none'){
        $('#add-item-section')[0].style.display = 'block';
        window.location.hash ='#add-item-section';
    }
});

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
            alert('Something missing! PLease refill the form');
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
            alert('Something missing! PLease refill the form');
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
            alert('Something missing! PLease refill the form');
        }
    });
};

// Confirm Booking

function confirm_booking (id) {

    id = id;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/confirm-booking/',
        data: {
            'booking-id' : $('input[name=booking-id-'+id+']').val(),
            'csrfmiddlewaretoken': $('input[name=csrf]').val(),
            'category' : $('input[name=category-'+id+']').val(),
            'rooms' : $('select[name=alloted-rooms-'+id+']').val(),
        },
        success: function(data) {
            alert("Success");
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
};

// Reject Booking

function reject_booking (id) {

    id = id;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/reject-booking/',
        data: {
            'booking-id' : $('input[name=booking-id-'+id+']').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        },
        success: function(data) {
            alert("Rejected");
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
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
            alert("Success");
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
});

// Submit Visitor Details

function submit_visitor_details (id, i) {
    id = id;
    i = i;
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/check-in/',
        data: {
            'booking-id' : id,
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'name' : $('input[name=visitor-name-'+id+'-'+i+']').val(),
            'phone' : $('input[name=phone-'+id+'-'+i+']').val(),
            'email' : $('input[name=email-'+id+'-'+i+']').val(),
            'address' : $('input[name=address-'+id+'-'+i+']').val()
        },
        success: function(data) {
            alert("Success");
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
}

// Check Out

function check_out (id) {
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/check-out/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'id' : id,
        },
        success: function(data) {
            alert("Checked Out");
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
}

function find_available_rooms () {
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
            alert('Something missing! PLease refill the form');
        }
    });
}

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
            alert("Forwarded")
        },
        error: function(data, err) {
            alert('Something missing! PLease refill the form');
        }
    });
}
