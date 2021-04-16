import asyncio
import logging
import os

import RPi.GPIO as GPIO
import yaml

from modules.init_cameras import Camera
from modules.listen_to_robonomics import listener


def read_configuration(dirname_f: str) -> dict:
    """
    :param dirname_f: path to the project ending with .../cameras_robonomics
    :type dirname_f: str
    :return: dictionary containing all the configurations
    :rtype: dict

    Reading config, containing all the required data, such as filepath, robonomics parameters (remote wss, seed),
    camera parameters (ip, login, password, port), etc
    """
    config_path = dirname_f + "/config/config.yaml"
    logging.debug(config_path)

    try:
        with open(config_path) as f:
            content = f.read()
            config_f = yaml.load(content, Loader=yaml.FullLoader)  #
            logging.debug(f"Configuration dict: {content}")
            return config_f
    except Exception as e:
        while True:
            logging.error("Error in configuration file!")
            logging.error(e)
            exit()


class Error(Exception):
    pass


if __name__ == "__main__":
    dirname = os.path.dirname(os.path.abspath(__file__))  # get path ending with .../cameras_robonomics
    config = read_configuration(dirname)
    cam = Camera(config)  # create an instance of Camera class. Class described in modules/init_cameras.py
    channel = 18  # gpio pin to be wired with button
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # rising edge
    GPIO.add_event_detect(
        channel,
        GPIO.BOTH,  # both, offs and ons
        callback=lambda x: listener(channel, config, cam, dirname),
        bouncetime=1000,  # avoid trigger current bouncing
    )  # Setup event on pin 18 rising edge. Standard snippet to detect gpio events
    loop = asyncio.get_event_loop()
    loop.run_forever()  # these two lines are to prevent python from exiting the script. JUst waits infinitely for
    # GPIO events
    print("Waiting for button to be pressed")  # Run until someone presses enter

    GPIO.cleanup()  # Clean up
