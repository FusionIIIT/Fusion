import base64
import io
import urllib

from django import template

register = template.Library()

@register.filter
def get64(url):
    """
    Method returning base64 image data instead of URL
    """
    if url.startswith("http"):
        image = io.StringIO(urllib.urlopen(url).read())
        return 'data:image/jpg;base64,' + base64.b64encode(image.read())

    return url
