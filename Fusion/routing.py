from channels.routing import route
from notification_channels.consumers import add, disconnect, message

channel_routing = [
    route("websocket.connect", add, path=r"/notifications/"),
    # path="r^/(?P<room_name>[a-zA-Z0-9_]+)/$"),
    route("websocket.disconnect", disconnect, path=r"/notifications/"),
    route("websocket.receive", message, path=r"/notifications/"),
]
