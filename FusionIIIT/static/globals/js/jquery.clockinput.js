/**
 * @name        jquery.clockInput
 * @author      Sheng-Liang Slogar <slogar.sheng@gmail.com>
 * @version     0.0.1
 * @link        https://github.com/shengslogar/jquery.clockInput
 * @requires    jQuery, helper CSS
 * @description Transforms input=time into a circular clock
 */

(function ($) {

    // expands inputs, left padding with 0 to desired length
    function forceLength(str, len) {
        str = str.toString();
        var diff = len - str.length;

        for (var i = 0; i < diff; i++)
            str = '0' + str;

        return str;
    }

    $.fn.clockInput = function (DISABLE_MINUTES) {

        var MODE_HOURS = 0,
            MODE_MINUTES = 1;

        // hide input
        var $this = $(this);
        $this.addClass("jq-ci-p");

        var date;
        var dateIsPM;

        var hoursMax = 23,
            hoursMin = 00,
            minutesMax = 59,
            minutesMin = 00;

        // parse min and max attribs
        if ($this.attr("max")) {
            var max = $this.attr("max").split(":");

            hoursMax = Number(max[0]);
            minutesMax = Math.round(max[1] / 5) * 5; // round to nearest 5
        }

        if ($this.attr("min")) {
            var min = $this.attr("min").split(":");
            hoursMin = Number(min[0]);
            minutesMin = Math.round(min[1] / 5) * 5; // round to nearest 5
        }

        // error validation
        if (hoursMin > hoursMax || (hoursMin == hoursMax && minutesMin > minutesMax)) {
            console.error("Improper bounds. input.min attribute must be less than or equal to input.max.");
            return; // break
        }

        // create parent
        var $parent = $('<div>', {'class': 'jq-ci'});

        // switch clock display to corresponding mode
        function changeMode(modeID) {

            // reset
            $parent.removeClass('jq-ci--h jq-ci--m');

            switch (modeID) {
                case MODE_HOURS:
                    $parent.addClass('jq-ci--h');

                    break;

                case MODE_MINUTES:
                    if (!DISABLE_MINUTES)
                        $parent.addClass('jq-ci--m');
                    else
                        changeMode(MODE_HOURS); // go back

                    break;
            }
        }

        // init
        changeMode(MODE_HOURS);

        // time indicator
        var $time = $('<div>', {'class': 'jq-ci-t'});
        $parent.append($time);

        var $time_h = $('<span>', {html: '--', 'class': 'jq-ci-t_h'}).click(function () {
            changeMode(MODE_HOURS);
        });

        var $time_m = $('<span>', {html: '--', 'class': 'jq-ci-t_m'}).click(function () {
            changeMode(MODE_MINUTES);
        });

        var $time_ap = $('<span>', {html: '<span>AM</span><span>PM</span>', 'class': 'jq-ci-t_ap'}).click(function () {
            date.setHours(date.getHours() + (date.getHours() >= 12 ? -12 : 12));
            refresh();
        });

        $time.append($time_h).append(":").append($time_m).append($time_ap);

        // updates all dates/times based off of `date` var
        function refresh(loadFromVal) {

            if (loadFromVal)
                date = new Date(Date.parse('0 ' + $this.val()) || 0);

            // cleanup
            date.setSeconds(0);
            date.setMilliseconds(0);

            var hours = date.getHours();

            // reset if out of range
            if (hours < hoursMin)
                hours = hoursMin;
            else if (hours > hoursMax)
                hours = hoursMax;

            date.setHours(hours); // update

            // ampm
            dateIsPM = date.getHours() > 11;

            if (dateIsPM)
                $time_ap.addClass('jq-ci-t_ap--s');
            else
                $time_ap.removeClass('jq-ci-t_ap--s');

            $hours.children().removeClass('jq-ci-h_h--s jq-ci-hide');
            hour_items[hours - (dateIsPM ? 12 : 0)].addClass('jq-ci-h_h--s');
            $time_h.html(hours == 0 ? 12 : (hours - (hours > 12 ? 12 : 0)));

            // hide out of range selections
            for (var i = 0; i < hoursMin; i++) {
                if (i >= 12 && dateIsPM)
                    hour_items[i - 12].addClass('jq-ci-hide');
                else if (i < 12 && !dateIsPM)
                    hour_items[i].addClass('jq-ci-hide');
            }

            for (var i = hoursMax; i < 24; i++) {
                // if max is 6 but minutes are 40, we still need
                // to show 6
                if (i > (hoursMax + (minutesMax / 60))) {
                    if (i >= 12 && dateIsPM) {
                        hour_items[i - 12].addClass('jq-ci-hide');
                    }
                    else if (i < 12 && !dateIsPM) {
                        hour_items[i].addClass('jq-ci-hide');
                    }
                }
            }

            // minutes
            var minutes = Math.round(date.getMinutes() / 5) * 5; // round to nearest five

            // contain bounds
            if (hours == hoursMax && minutes > minutesMax)
                minutes = minutesMax;
            else if (hours == hoursMin && minutes < minutesMin)
                minutes = minutesMin;

            date.setMinutes(minutes); // update

            $minutes.children().removeClass('jq-ci-m_m--s jq-ci-hide');
            minute_items[minutes / 5].addClass('jq-ci-m_m--s');
            $time_m.html(forceLength(minutes, 2));

            // hide out of range selections
            if (hours == hoursMax) {
                for (var i = minutesMax + 5 /* start hiding *after* max */; i < 60; i += 5) {
                    minute_items[i / 5].addClass('jq-ci-hide');
                }
            }

            // prev version has elseif here.
            // this doesn't work if hoursMin == hoursMax
            if (hours == hoursMin) {
                for (var i = 0; i < minutesMin; i += 5) {
                    minute_items[i / 5].addClass('jq-ci-hide');
                }
            }

            // update html input
            var newVal = forceLength(date.getHours(), 2) + ":" + forceLength(date.getMinutes(), 2);

            if (newVal != $this.val())
                $this.val(newVal).trigger('change');
        }

        // hours
        var $hours = $('<div>', {'class': 'jq-ci-h'});
        var hour_items = [];
        $parent.append($hours);

        $hours.on('click', 'span', function () {
            var newHr = (Number)($(this).text());

            if (newHr == 12)
                newHr = 0;

            newHr += (dateIsPM ? 12 : 0);

            date.setHours(newHr);
            refresh();
            changeMode(MODE_MINUTES);
        });

        // add hours
        (function () {
            for (var i = 0; i < 12; i++) {
                var $kid = $('<span>', {'class': 'jq-ci-h_h jq-ci-h_h--' + i, html: (i == 0 ? 12 : i)});
                hour_items.push($kid);
                $hours.append($kid);
            }
        }());

        // minutes
        var $minutes = $('<div>', {'class': 'jq-ci-m'});
        var minute_items = [];
        $parent.append($minutes);

        $minutes.on('click', 'span', function () {
            date.setMinutes((Number)($(this).text()));
            refresh();
        });

        // add minutes
        (function () {
            for (var i = 0; i < 60; i += 5) {
                var $kid = $('<span>', {'class': 'jq-ci-m_m jq-ci-m_m--' + i, html: forceLength(i, 2)});
                minute_items.push($kid);
                $minutes.append($kid);
            }
        }());

        // append
        $this.after($parent).change(function () {
            refresh();
        });

        // init
        refresh(true);

        return this;
    };
}(jQuery));