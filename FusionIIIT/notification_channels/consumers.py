from channels import Group
from channels.auth import channel_session_user, channel_session_user_from_http


@channel_session_user
def message(message):
    pass
    # mes = parse_qs(message.content['text'])


@channel_session_user_from_http
def add(message):
    if(message.user.is_authenticated()):
        Group(message.user.username).add(message.reply_channel)
        message.reply_channel.send({"accept": True})
    else:
        message.reply_channel.send({"accept": False})


@channel_session_user
def disconnect(message):
    Group(message.user.username).discard(message.reply_channel)
