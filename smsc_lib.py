import re
from urllib.parse import unquote_plus
from more_itertools import first


def decode_message(message):
    decoded_message = message.decode('utf-8')
    text_message = first(
        re.findall('[^text=].*', decoded_message), ''
    )
    return unquote_plus(text_message)
