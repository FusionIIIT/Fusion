$.suiAlert = function (permanents) {
    var options = $.extend({
        title: 'Semantic UI Alerts',
        description: 'semantic ui alerts library',
        // alert types 'info, success, error, warning'
        type: "error",
        time: 5,
        position: "top-right",
        icon: false,
    }, permanents);

    // set alert icon
    if (options.icon === false) {
        if (options.type == "info") {
            // announcement
            options.icon = "announcement";
        } else if (options.type == "success") {
            // checkmark, checkmark box
            options.icon = "checkmark";
        } else if (options.type == "error") {
            // ban, remove, remove circle
            options.icon = "remove";
        } else if (options.type == "warning") {
            // warning sign, warning circle
            options.icon = "warning circle";
        }
    }

    // set close animation
    var close_anim = "drop";
    if (options.position == "top-right") {
        close_anim = "fly left";
    } else if (options.position == "top-center") {
        close_anim = "fly down";
    } else if (options.position == "top-left") {
        close_anim = "fly right";
    } else if (options.position == "bottom-right") {
        close_anim = "fly left";
    } else if (options.position == "bottom-center") {
        close_anim = "fly up";
    } else if (options.position == "bottom-left") {
        close_anim = "fly right";
    }

    // screen size check
    var alert_size = '';
    var screen_width = $(window).width();
    if (screen_width < 425)
        alert_size = 'mini';

    var alerts_class = "ui-alerts." + options.position;
    if (!$('body > .' + alerts_class).length) {
        $('body').append('<div class="ui-alerts ' + options.position + '"></div>');
    }

    var _alert = $('<div class="ui icon floating ' + alert_size + ' message ' + options.type + '" id="alert"> <i class="' + options.icon + ' icon"></i> <i class="close icon" id="alertclose"></i> <div class="content"> <div class="header">' + options.title + '</div> <p>' + options.description + '</p> </div> </div>');
    $('.' + alerts_class).prepend(_alert);

    _alert.transition('pulse');

    /**
     * Close the alert
     */
    $('#alertclose').on('click', function () {
        $(this).closest('#alert').transition({
            animation: close_anim,
            onComplete: function () {
                _alert.remove();
            }
        });
    });

    var timer = 0;
    $(_alert).mouseenter(function () {
        clearTimeout(timer);
    }).mouseleave(function () {
        alertHide();
    });

    alertHide();

    function alertHide() {
        timer = setTimeout(function () {
            _alert.transition({
                animation: close_anim,
                duration: '2s',
                onComplete: function () {
                    _alert.remove();
                }
            });
        }, (options.time * 1000));
    }
};
