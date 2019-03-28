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
            'booking_from' : $('input[name="booking-from"]').val(),
            'booking_to' : $('input[name="booking-to"]').val(),
            'number-of-people' : $('input[name="number-of-people"]').val(),
            'purpose-of-visit' : $('input[name="purpose-of-visit"]').val(),
        },
        success: function(data) {
            $('#request-booking-form')[0].reset();
        },
        error: function(data, err) {
            alert(err.message);
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
    console.log(food);
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/bookmeal/',
        data: {
            'pk' : pk,
            'numberofpeople': $('input[name="numberofpeople-meal"]').val(),
            'food':food,
            'csrfmiddlewaretoken': '{{csrf_token}}'
        },
        success: function(data) {
            alert('aya');
        },
        error: function(data, err) {
            alert(err.message);
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
            alert(err.message);
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
            alert(err.message);
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
            alert(err.message);
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
            alert(err.message);
        }
    });
};

// Confirm Booking

$('#confirm-booking').click(function(event){
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/confirm-booking/',
        data: {
            'booking-id' : $('input[name="booking-id"]').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
            'category' : $('input[name="category"]').val(),
        },
        success: function(data) {
            alert("Success");
        },
        error: function(data, err) {
            alert(err.message);
        }
    });
});

// Reject Booking

$('#reject-booking').click(function(event){
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/reject-booking/',
        data: {
            'booking-id' : $('input[name="booking-id"]').val(),
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        },
        success: function(data) {
            window.reload()
        },
        error: function(data, err) {
            alert(err.message);
        }
    });
});

// Check In

$('#checkin-submit').click(function(event){
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/bookaroom/',
        data: {
            'csrfmiddlewaretoken' : '{{csrf_token}}',
            'name' : $('input[name="name"]').val(),
            'organisation' : $('input[name="organisation"]').val(),
            'phone' : $('input[name="phone"]').val(),
            'email' : $('input[name="email"]').val(),
            'address' : $('textarea[name="address"]').val(),
            'category' : $('input[name="category"]').val(),
            'country' : $('input[name="country"]').val(),
            'numberofpeople' : $('input[name="numberofpeople"]').val(),
            'numberofrooms' : $('input[name="numberofrooms"]').val(),
            'purposeofvisit' : $('textarea[name="purposeofvisit"]').val(),
            'booking_from' : $('input[name="booking_from"]').val(),
            'booking_to' : $('input[name="booking_to"]').val()
        },
        success: function(data) {
            alert("Success");
            $('#bookaroom-form')[0].reset();
        },
        error: function(data, err) {
            alert(err.message);
        }
    });
});

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
            alert(err.message);
        }
    });
});
