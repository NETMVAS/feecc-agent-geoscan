import logging
import sys
import time
from threading import Thread

import RPi.GPIO as GPIO

from modules.init_cameras import Camera
from modules.link_to_printer import Task
from modules.qr_generator import create_qr
from modules.send_to_ipfs import send
from modules.url_generator import create_url


def listener(channel: int, config: dict, cam: Camera, dirname: str) -> None:
    """
    :param channel: pin on RPI GPIO panel. See RPI documentation for more
    :type channel: int
    :param config: dictionary containing all the configurations
    :type config: dict
    :param cam: an instance of a class, containing all its parameters and methods specified in init_cameras.py
    :type cam: Camera
    :param dirname: path to the project ending with .../cameras_robonomics
    :type dirname: str

    This function is a callback for GPIO events. When 'on', is starts a thread to record video, another thread to print
    qr. When 'off', raises a flag to stop recording and start a thread to send file to ipfs, upload it to pinata etc.
    """
    time.sleep(0.1)  # catch power surges
    if not GPIO.input(channel):  # if trigger is in on position
        if cam.initial_launch:
            cam.initial_launch = False
        if cam.is_busy:
            logging.warning("Camera is busy. Record aborted")
            return None
        # chek that the script was not launched with a trigger in on position and that camera is not fi;ming right now
        cam.stop_record = False
        cam.is_busy = True
        # state that camera is filming now. clear stop flag
        start_record_cam_thread = Thread(
            target=start_record_cam,  # function calling record method of Camera class
            args=(
                cam,
                dirname,
            ),
        )  # thread to start recording. Threads are used to be able to detect future events on GPIO, print qr-code  and
        # to avoid looping main thread
        start_record_cam_thread.start()
        create_url_r_thread = Thread(
            target=create_url_r,
            args=(
                cam,
                dirname,
                config,
            ),
        )  # thread to print qr-code as soon as the recording starts.
        create_url_r_thread.start()

    else:
        if cam.initial_launch:
            cam.initial_launch = False
            return None
        if not cam.is_busy:
            logging.warning("Camera is not recording. Nothing to stop")
            return None
        cam.stop_record = True  # raise the stop flag so that the record method of Camera interrupts recording
        cam.is_busy = False  # checking some conditions similar to start signal and starting stopping (:D) thread
        stop_record_cam_thread = Thread(
            target=stop_record_cam,
            args=(
                cam.filename,
                cam.keyword,
                cam.qrpic,
                config,
                dirname,
            ),
        )
        stop_record_cam_thread.start()


def start_record_cam(cam: Camera, dirname: str) -> None:
    """
    :param cam: an instance of a class, containing all its parameters and methods specified in init_cameras.py
    :type cam: Camera
    :param dirname: path to the project ending with .../cameras_robonomics
    :type dirname: str
    """
    cam.record(dirname)
    sys.exit()  # exiting the thread after recording to liberate system resources


def stop_record_cam(filename: str, keyword: str, qrpic: str, config: dict, dirname: str) -> None:
    """
    :param filename: name of a resulted video
    :type filename: str
    :param keyword: shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
    :type keyword: str
    :param qrpic: name of a qr-code file. Qr-code, which is redirecting to IPFS gateway
    :type qrpic: str
    :param config: dictionary containing all the configurations
    :type config: dict
    :param dirname: path to the project ending with .../cameras_robonomics
    :type dirname: str
    """
    time.sleep(1)
    send(filename, keyword, qrpic, config, dirname)  # start the process of publishing the file to ipfs etc
    sys.exit()  # exiting the thread after recording to liberate system resources


def create_url_r(cam: Camera, dirname: str, config: dict) -> None:
    """
    :param cam: an instance of a class, containing all its parameters and methods specified in init_cameras.py
    :type cam: Camera
    :param dirname: path to the project ending with .../cameras_robonomics
    :type dirname: str
    :param config: dictionary containing all the configurations
    :type config: dict
    """
    cam.keyword, cam.link = create_url(config)  # creating url to print it further. More in url_generator.py
    logging.warning(cam.link)
    cam.qrpic = create_qr(dirname, cam.link, config)  # create qr-code encoding the short url from yourls.
    # More in qr_generator.py
    if config["print_qr"]["enable"]:
        Task(cam.qrpic)  # print the qr-code. more in link_to_printer.py
