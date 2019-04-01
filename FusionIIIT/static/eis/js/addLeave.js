$(document).ready(function() {
    $('.ui.checkbox')
        .checkbox()
    ;
});

function addLeave() {
    var parent = document.getElementById('applyLeave');

    var row = document.createElement("div");
    row.className = 'ui row';

    var fields = document.createElement("div");
    fields.className = 'fields';

    var fromField = document.createElement("div");
    fromField.className = 'four wide field';

    var toField = document.createElement("div");
    toField.className = 'four wide field';

    var leaveTypeField = document.createElement("div");
    leaveTypeField.className = 'six wide field';

    var slField = document.createElement("div");
    slField.className = 'field';

    var leaveFrom = document.createElement("input");
    leaveFrom.setAttribute("type", "text");
    leaveFrom.setAttribute("placeholder","From");

    var leaveTo= document.createElement("input");
    leaveTo.setAttribute("type", "text");
    leaveTo.setAttribute("placeholder","To");

    var slDiv = document.createElement('div');
    slDiv.className = 'ui toggle checkbox';

    var requiredText = document.createTextNode("Required");

    var label = document.createElement('label');
    label.appendChild(requiredText);

    var slSlider = document.createElement("input");
    slSlider.setAttribute("type", "checkbox");

    parent.appendChild(row);
    row.appendChild(fields);
        fields.appendChild(fromField);
            fromField.appendChild(leaveFrom);
        fields.appendChild(toField);
            toField.appendChild(leaveTo);
        fields.appendChild(leaveTypeField);
        fields.appendChild(slField);
            slField.appendChild(slDiv);
                slDiv.appendChild(slSlider);
                slDiv.appendChild(label);
}
