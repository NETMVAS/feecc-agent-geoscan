import logging
import time
import subprocess


class Camera:
    def __init__(self, config: dict) -> None:
        """
        :param config: dictionary containing all the configurations
        :type config: dict

        Class description. On initiating state some attributes and methods to be described below
        """
        self.qrpic = None  # future path to qr-code picture file. This will be used to create a labels
        self.keyword = None  # shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
        self.ip = config["camera"]["ip"]  # dictionary containing all the configurations
        self.port = config["camera"]["port"]  # port where the camera streams, required for rtsp
        self.login = config["camera"]["login"]  # camera login to obtain access to the stream
        self.password = config["camera"]["password"]  # camera password to obtain access to the stream

        self.initial_launch = True  # needed for the first launch for the situation if the trigger is in on position
        self.is_busy = False  # stating that in the beginning camera is not filming
        self.stop_record = False  # no stop filming flag raised

    def record(self, dirname: str) -> None:
        """
        :param dirname: path to the project ending with .../cameras_robonomics
        :type dirname: str

        main method to record video from camera. Uses popen and ffmpeg utility
        """
        self.filename = (
                dirname + "/output/" + time.ctime(time.time()).replace(" ", "_") + ".mp4"
        )  # new video filepath. It is to be saved in a separate directory with a timestamp
        self.program_ffmpeg = (
                'ffmpeg -rtsp_transport tcp -i "rtsp://'  # using rtsp to get stream
                + self.login
                + ":"
                + self.password
                + "@"
                + self.ip
                + ":"
                + self.port
                + '/Streaming/Channels/101" -r 25 -c copy -map 0 '
                + self.filename
        )  # the entire line looks like
        # ffmpeg -rtsp_transport tcp -i "rtsp://login:password@ip:port/Streaming/Channels/101" -c copy -map 0 vid.mp4
        # more on ffmpeg.org
        self.process_ffmpeg = subprocess.Popen(
            "exec " + self.program_ffmpeg,
            shell=True,  # execute in shell
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,  # to get access to all the flows
        )
        logging.warning("Started recording image")
        while not self.stop_record:
            continue  # camera will be recording till the flag is raised. It happens when the trigger goes in off
        logging.warning("Stopped recording image")
        time.sleep(1)  # some time to finish the process
        self.process_ffmpeg.kill()  # kill the subprocess to liberate system resources
