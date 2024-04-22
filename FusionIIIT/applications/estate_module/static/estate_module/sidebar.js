$(document).ready(function () {
    $('#messages')
        .find('.message')
        .each(function () {
            $.uiAlert({
                textHead: $(this).attr('message'), // header
                text: '',
                bgcolor: $(this).attr('tag'), // background-color
                textcolor: '#fff', // color
                position: 'bottom-left', // position . top And bottom ||  left / center / right
                time: 3, // time
            });
        });

    $('#new-notification').popup({
        inline: true,
        hoverable: true,
        position: 'bottom left',
        popup: $('#notificationPopup'),
        on: 'click',
        delay: {
            show: 250,
            hide: 500,
        },
    });
});
$(document).ready(function () {
    newNotification();
    newNotification();
    newNotification();

    $('.ui.accordion').accordion('refresh');
    $('.ui.sidebar')
        //.sidebar('toggle')
        .sidebar('attach events', '#navbar #sidebartrigger')
        .sidebar('setting', 'transition', 'overlay');
});
function newNotification() {
    console.log('A new Notification added!');

    var notifactionName = document.createTextNode('Kanishka Munshi');
    var notificationEmail = document.createTextNode('gmail@zlatan.com');
    var notificationMessage = document.createTextNode(
        'I have decided to go on a leave!'
    );
    var space = document.createElement('br');

    var parent = document.getElementById('new-message-list');

    var itemDiv = document.createElement('div');
    itemDiv.className = 'item';

    var contentDiv = document.createElement('div');
    contentDiv.className = 'content';

    var descriptionDiv = document.createElement('div');
    descriptionDiv.className = 'description';

    var headerAnchor = document.createElement('a');
    headerAnchor.className = 'ui header';

    var userAvatar = document.createElement('img');
    userAvatar.src = '/static/globals/img/zlatan.jpg';
    userAvatar.className = 'ui circular image right floated';

    var dividerDiv = document.createElement('div');
    dividerDiv.className = 'ui divider';

    parent.appendChild(itemDiv);
    itemDiv.appendChild(contentDiv);
    headerAnchor.appendChild(userAvatar);
    contentDiv.appendChild(headerAnchor);
    contentDiv.appendChild(descriptionDiv);
    parent.appendChild(dividerDiv);

    headerAnchor.appendChild(notifactionName);
    descriptionDiv.appendChild(notificationEmail);
    descriptionDiv.appendChild(space);
    descriptionDiv.appendChild(notificationMessage);
}
