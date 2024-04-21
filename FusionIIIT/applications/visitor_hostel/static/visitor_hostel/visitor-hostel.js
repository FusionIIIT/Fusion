// Global date variable for today's date

var d = new Date();
var date = d.getFullYear() + "-" + (d.getMonth()+1) + "-" + d.getDate();

// Date settings for Semantic UI

$(document).ready(function(){

    // $('.delete').hide(); 
    // // Deleting an Individual Service
    // $('.intender_entry_row').hover( function() {
    //     $(this).find(".delete").show();
    // });
    
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
    arrival_hour = $('input[name="arrival-hour"]').val();
    arrival_minute = $('input[name="arrival-minutes"]').val();
    arrival = $('input[name="arrival"]').val();
    departure_hour = $('input[name="departure-hour"]').val();
    departure_minute = $('input[name="departure-minutes"]').val();
    departure = $('input[name="departure"]').val();
    number_of_people =  parseInt($('input[name="number-of-people"]').val());
    number_of_rooms =  parseInt($('input[name="number-of-rooms"]').val());
    purpose_of_visit = $('input[name="purpose-of-visit"]').val();
    remarks_during_booking_request = $('input[name="remarks-during-booking-request"]').val();
    bill_settlement = $('input[name="bill_settlement"]').val();

    booking_from_time = arrival_hour.concat(":").concat(arrival_minute).concat(" ").concat(arrival);
    booking_to_time = departure_hour.concat(":").concat(departure_minute).concat(" ").concat(departure);

// visitor details
    name = $('input[name=visitor-name-1]').val();
    phone = $('input[name=phone-1]').val();
    email = $('input[name=email-1]').val();
    address = $('input[name=address-1]').val();
    organization = $('input[name=organization-1]').val();
    nationality = $('input[name=country]').val();

    // Conditions for arival and departure time
    if ( ! booking_from ) {
        alertModal ("Please fill expected arrival date!");
        return;
    }

    if ( !arrival_hour) {
        alertModal ('Oops! Please enter the expected arrival hour of the visitor');
        return;
    }

    // Arrival hour and minutes converted

    if ( !arrival_minute) {
        alertModal ('Oops! Please enter the expected arrival minutes of the visitor');
        return;
    }

    if ( !arrival) {
        alertModal ('Oops! Please enter the expected arrival time of the visitor');
        return;
    }

    if ( ! booking_to)  {
        alertModal ("Please fill expected departure date!");
        return;
    }

    if ( !departure_hour) {
        alertModal ('Oops! Please enter the expected departure hour of the visitor');
        return;
    }
    if ( !departure_minute) {
        alertModal ('Oops! Please enter the expected departure minutes of the visitor');
        return;
    }

    if ( !departure) {
        alertModal ('Oops! Please enter the expected departure time of the visitor');
        return;
    }

    // if date is less than today's date
    if (new Date(booking_from) < new Date(date)) {
        alertModal ('Oops! Those dates are not available for booking.');
        return;
    }

    if (new Date(booking_from) >new Date(booking_to)) {
        alertModal ('Please check start date and end date!');
        return;
    }

    // if duration of booking is greater than 15 days

    if ( days_diff > 15 ) {
        alertModal ('You are only allowed to book a room for 15 days!');
        return;
    }

    if ( !number_of_people ) {
        alertModal ("Please fill number of people!");
        return;
    }

    if ( !number_of_rooms ) {
        alertModal ("Please fill required number of rooms!");
        return;
    }

    if (number_of_people < 1 ) {
        alertModal ("Oops! People can't be zero or negative in number.");
        return;
    }

    if( number_of_rooms > number_of_people ) {
        console.log(number_of_rooms + " and people " + number_of_people)
        alertModal("Oops! Number of rooms can not be greater than number of people.");
        return;
    }

    // if number of people greater than 20
    
    if (number_of_people > 20) {
        alertModal ("Oops! People can't be greater than 20 in number.");
        return;
    }

    if (number_of_rooms < 1) {
        alertModal ("Oops! Number of rooms can't be zero or negative.");
        return;
    }

    if (number_of_rooms > 15) {
        alertModal ("Oops! Number of rooms can't be greater than 15.");
        return;
    } 

    if ( !category ) {
        alertModal ("Please fill the Category!");
        return;
    } 

    if ( !nationality ) {
         nationality = ' ';
    }
    console.log(nationality) 

    // Checking conditions for visitor
    
    if (name == '') {
            alertModal("You didn't fill a visitor name! Please refill the form.");
            return;
    }

    if (phone == '') {
        alertModal("You didn't fill a visitor's phone number. Please fill the form again.");
        return;
    }
    //phone = $('input[name="phoneNum"]').val();

    today = new Date();
    dd = today.getDate();

    var oneDay = 24*60*60*1000; // hours*minutes*seconds*milliseconds
    var firstDate = new Date(booking_from);
    var secondDate = new Date(booking_to);

    var days_diff = Math.round(Math.abs((firstDate.getTime() - secondDate.getTime())/(oneDay)));

    if (!(/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email))){
        alertModal("Oops! Please enter valid email address.");
        return;
    }

    if (phone < 1000000000){
        alertModal("Oops! Please enter valid phone number.");
        return;
    }

    if (phone.length!=10){
        alertModal("Oops! Please enter valid phone number.");
        return;
    }

    

    if ( !arrival_hour) {
        alertModal ('Oops! Please enter the expected arrival time of the visitor');
        return;
    }

    if ( !arrival_minute) {
        alertModal ('Oops! Please enter the expected arrival time of the visitor');
        return;
    }

    if ( !arrival) {
        alertModal ('Oops! Please enter the expected arrival time of the visitor');
        return;
    }

    if ( !departure_hour) {
        alertModal ('Oops! Please enter the expected departure time of the visitor');
        return;
    }
    if ( !departure_minute) {
        alertModal ('Oops! Please enter the expected departure time of the visitor');
        return;
    }

    if ( !departure) {
        alertModal ('Oops! Please enter the expected departure time of the visitor');
        return;
    }



    // Ajax call

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
               'category' : category,
               'booking_from_time' : booking_from_time,
               'booking_to_time' : booking_to_time,
               'remarks_during_booking_request': remarks_during_booking_request,
               'bill_settlement' : bill_settlement,
               'name' : name,
                'phone' : phone,
                'email' : email,
                'address' : address,
                'nationality' : nationality,
                'organization' : organization,
         },
        success: function(data,err) {
            console.log(name + " " + phone + " " + email + " " + address + " " +nationality + " " + organization);
            alertModal(" Congratulations! Your booking has been placed successfully\n Please wait for confirmation");
            console.log(booking_to_time);
            setTimeout(function() {
                location.reload();
             }, 1500);
           
        },
        error: function(data, err) {
            console.log(name + " " + phone + " " + email + " " + address);
            alertModal('Congratulations! Your booking has been placed successfully\n Please wait for confirmation.');
          
        }
    });
};


// Meal Record

function bookameal_submit(event, htmlElement){
    console.log('hii')
    event.preventDefault();
    var pk = $(htmlElement).attr('data-pk');
    var booking_id = $(htmlElement).attr('booking_id')
    // 'numberofpeople': $('input[name="numberofpeople-meal"]').val(),
    console.log(pk);
    var jsondata = {
            'pk' : pk,
            'booking' : booking_id,
        'm_tea': $(`input[name="m_tea${booking_id}"]`).val(),
        'breakfast': $(`input[name="breakfast${booking_id}"]`).val(),
        'lunch': $(`input[name="lunch${booking_id}"]`).val(),
        'eve_tea': $(`input[name="eve_tea${booking_id}"]`).val(),
        'dinner': $(`input[name="dinner${booking_id}"]`).val(),
            
            'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
    }
    console.log(jsondata)
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/record-meal/',
        data: jsondata,
        success: function(data) {
            alertModal('Great! Meals recorded successfully');
            setTimeout(function() {
                location.reload();
             }, 1500);
            
        },
        error: function (data, err) {
            alertModal('Something missing! Please refill the form ');
        }
    });
};

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

// Adding more items to inventory

// $('#add-more-items-inventory').click(function(event){

//     $.ajax({
//         type: 'POST',
//         url: '/visitorhostel/add-to-inventory/',
//         data: {
//             'item' : $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value,
//             'quantity' : $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value,
//             'amount' : $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value,
//             'consumable' : $('.reset-this-form')[0].children[2].children[3].children[1].children[0].value,
//             'csrfmiddlewaretoken': '{{csrf_token}}'
//         },
//         success: function(data) {
//             $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value = "";
//             $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value = "";
//             $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value = "";
//         },
//         error: function(data, err) {
//             alertModal('Something missing! Please refill the form');
//         }
//     });

// });

function add_inventory_item(event) {
    event.preventDefault();
    jsondata = {
        'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        'item_name' : $('input[name="item_name"]').val(),
        'quantity' : $('input[name="quantity_add"]').val(),
        'cost' : $('input[name="cost"]').val(),
        'consumable': ($('input[name="consumable"]:checked').val())?true:false,
        'bill_number' : $('input[name="bill_number"]').val()
    }
    console.log(jsondata)
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/add-to-inventory/',
        data: jsondata,
        success: function(data) {
            // $('.reset-this-form')[0].children[2].children[0].children[1].children[0].value = "";
            // $('.reset-this-form')[0].children[2].children[1].children[1].children[0].value = "";
            // $('.reset-this-form')[0].children[2].children[2].children[1].children[0].value = "";
            alertModal('Great! Item added successfully');
            setTimeout(function() {
                location.reload();
             }, 1500);
        },
        error: function(xhr, data, err) {
            alertModal('Something missing! Please refill the form');
        }

    });
}
$('.add-item-form-submit').click(function(event){
    event.preventDefault();
    jsondata = {
        'csrfmiddlewaretoken': $('input[name="csrf"]').val(),
        'item_name' : $('input[name="item_name"]').val(),
        'quantity' : $('input[name="quantity_add"]').val(),
        'cost' : $('input[name="cost"]').val(),
        'consumable': ($('input[name="consumable"]:checked').val())?true:false,
        'bill_number' : $('input[name="bill_number"]').val()
    }
    console.log(jsondata)
    $.ajax({
        type: 'POST',
        url: '/visitorhostel/add-to-inventory/',
        data: jsondata,
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

// Confirm Booking by incharge

function confirm_booking (id) {

    csrfmiddlewaretoken = $('input[name=csrf]').val();
    category = $('input[name=category-'+id+']').val();
    rooms = $('select[name=alloted-rooms-'+id+']').val();

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
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Reject Booking by VhCaretaker

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
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};



// Update Booking

function update_booking (id) {


    intender = $('input[name="intender"]').val();
    category = $('input[name="visitor-category-'+id+'"]').val();
    csrfmiddlewaretoken = $('input[name="csrf"]').val();
    booking_from = $('input[name="update-booking-from"]').val();
    booking_to = $('input[name="update-booking-to"]').val();
    number_of_people = $('input[name="number-of-people-'+id+'"]').val();
    number_of_rooms = $('input[name="number-of-rooms-'+id+'"]').val();
    purpose_of_visit = $('input[name="purpose-of-visit-'+id+'"]').val();




    $.ajax({
        type: 'POST',
        url: '/visitorhostel/update-booking/',
        data: {
            'booking-id' : $('input[name=booking-id-'+id+']').val(),
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
            alertModal("This booking has been updated.");
            setTimeout(function() {
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            console.log(intender + " " + booking_from + " " + booking_to + " " + number_of_people+" "+purpose_of_visit+" "+ number_of_rooms);
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
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Forward Booking

// function forward_booking (id) {
//     id=id;
//     $.ajax({
//         type: 'POST',
//         url: '/visitorhostel/forward-booking/',
//         data: {
//             'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
//             'id' : id,
//         },
//         success: function(data) {
//             alertModal("This booking has been forwarded");
//             setTimeout(function() {
//                 window.location.replace('http://localhost:8000/visitorhostel');
//             }, 1500);
//         },
//         error: function(data, err) {
//             alertModal('Something missing! Please refill the form');
//         }
//     });
// }


// new forward booking

function forward_booking (id) {

    id=id;
    csrfmiddlewaretoken = $('input[name=csrf]').val();
    previous_category = $('input[name=category-'+id+']').val();
    modified_category = $('input[name=modified-category-'+id+']').val();
    rooms = $('select[name=alloted-rooms-'+id+']').val();
    rem = $('input[name=cancellation-remarks-' + id + ']').val();
    console.log("TExt rem: ", rem);
    // if (previous_category == 0) {
    //     alertModal("Please fill the category to confirm.");
    //     return;
    // }
    console.log("Rooms: ", rooms);
    remark = "";
    for (x in rooms) {
        remark += rooms[x] + " ";
    }
    remark += "can be alloted";

    console.log("remarks: ", remark);
    if (modified_category == 0) {
        modified_category = previous_category;
    }

    if (rooms == 0) {
        alertModal("Please fill the rooms to confirm booking.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/forward-booking/',
        data: {
            'id' : id,
            'csrfmiddlewaretoken': csrfmiddlewaretoken,
            'previous_category' : previous_category,
            'modified_category' : modified_category,
            'rooms': rooms,
            'remark': remark,
        },
        success: function(data) {
            alertModal("This booking has been forwarded");
            setTimeout(function() {
                location.reload();
            }, 1500);

        },
        error: function(data, err) {
            console.log(id + " " + previous_category + " "+ modified_category+ " " + rooms);
            alertModal('Something missing! Please refill the form');
        }
    });
};


// Cancel Active Booking by intender

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
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
};

// Edit Inventory

// $("#edit-inventory").click(function(e){
//     $(".inventory-item").slideToggle();
//     $(".inventory-form").slideToggle();
//     $("#update-inventory-submit").slideToggle();
// });
// $("#update-inventory-submit").click(function(e){
//     event.preventDefault();
//     $.ajax({
//         type: 'POST',
//         url: '/visitorhostel/bookaroom/',
//         data: {
//             'csrfmiddlewaretoken' : '{{csrf_token}}',
//             'data' : data
//         },
//         success: function(data) {
//             alertModal("Congratulations! Inventory is updated successfully");
//         },
//         error: function(data, err) {
//             alertModal('Something missing! PLease refill the form');
//         }
//     });
// });

// Submit Visitor Details

function submit_visitor_details (id) {
    vis_length = $('input[name=length-'+id+']').val();
    var temp = parseInt(vis_length);
    for (var i=1; i<=vis_length; i++) {
        csrfmiddlewaretoken = $('input[name="csrf"]').val();
        name = $('input[name=visitor-name-'+id+'-'+i+']').val();
        phone = $('input[name=phone-'+id+'-'+i+']').val();
        email = $('input[name=email-'+id+'-'+i+']').val();
        console.log(email);
        console.log("lll");
        address = $('input[name=address-'+id+'-'+i+']').val();

        if (name == '') {
            alertModal("You didn't fill a visitor name! Please refill the form.");
            return;
        }

        if (!(/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email))){
        alertModal("Oops! Please enter valid email address.");
        return;
        }

        if (phone == '') {
            alertModal("You didn't fill a visitor's phone number. Please fill the form again.");
            return;
        }

        // constraints on visitors phone number

        if (phone.length!=10){
            alertModal("Oops! Please enter valid phone number.");
            return;
        }

        if (phone < 1000000000){
            alertModal("Oops! Please enter valid phone number.");
            return;
        }
    }
    console.log(temp);
    // console.log(name + " " + phone + " " + email + " " + address);


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
                console.log(name + " " + phone + " " + email + " " + address);
                alertModal("Great! Visitor's details have been recorded successfully");
            },
            error: function(data, err) {
                console.log(name + " " + phone + " " + email + " " + address);
                alertModal('Something missing! Please refill the form');
            }
        });
    }
    setTimeout(function() {
        location.reload();
    }, 1500);
}

// Check Out

function check_out(id, mess_bill, room_bill) {
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
                location.reload();
            }, 1500);
        },
        error: function(data, err) {
            alertModal('Something missing! Please refill the form');
        }
    });
}

// bill records between a date range

function bill_between_date_range() {

    start = $('input[name=start]').val();
    end = $('input[name=end]').val();
    
    if(new Date(start)>new Date(end))
    {
        alertModal('Please check start date and end date.')
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/bill_between_dates/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),

            'start_date' : start,
            'end_date' : end,

        },
        success: function(data) {
            $('#replace-this-div-booking-bw-dates').html(data);
            console.log("winning");
            // alert('Bookings Between range are ..');
        },
        error: function(data, err) {
            alertModal ('Error !', data, err);
            // alertModal('Something missing! Please refill the form');
        }
    });
}

// finding available room's list between date range

function find_available_rooms ( available_rooms ) {
    start_date = $('input[name=start-date]').val();
    end_date = $('input[name=end-date]').val();
    if (new Date(start_date) > new Date(end_date)) {
        alertModal ('Please check start date and end date!');
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/visitorhostel/room-availability/',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrf"]').val(),
            'start_date' : start_date,
            'end_date' : end_date,

        },
        success: function(data) {
            $('#replace-this-div').html(data);
            console.log("winning");
            console.log(start_date);
            // alert('Bookings Between range are ..');
        },
        error: function(data, err) {
            alertModal ('Error !');
            console.log(start_date);
            console.log(end_date);
            // alertModal('Something missing! Please refill the form');

        }
    });
}

// next button in request booking form


function next_action(event){
    event.preventDefault();
    console.log("next!!");

    
    $("#booking-detail-data-tab").removeClass("active");
    $("#booking-detail-action-tab").removeClass("active");
    $("#visitor-detail-data-tab").addClass("active");
    $("#visitor-detail-action-tab").addClass("active");
}

// next button in request action form

function next_button_action_form(event){
    event.preventDefault();
    console.log("next!!@@@");

    
    $("#booking-detail-action-data-tab").addClass("active");
    $("#booking-detail-action-form-tab").addClass("active");
    $("#visitor-detail-action-data-tab").removeClass("active");
    $("#visitor-detail-action-form-tab").removeClass("active");
}



// Various Modals

function modalAddItem(){
    $('#addItemModal').modal('show');
}

function bookingRequestModal(id){
    $('#booking-request-'.concat(id)).modal('show');
}

function updateBookingModal(id){
    $('#update-booking-'.concat(id)).modal('show');
}

function cancellationRequestModal(id) {
    $('#cancellation-request-'.concat(id)).modal('show');
}

function bookingDetailsModal(id){
    console.log("booking detail modal! ");
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
function hostelBillModal(id) {
    console.log("in visitor-hostel.js")
    $('#hostel-bill-'.concat(id)).modal('show');
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

