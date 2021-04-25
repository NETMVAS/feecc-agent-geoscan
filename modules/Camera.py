import logging
import subprocess
import time
from os import path
import typing as tp

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Camera:
    def __init__(self, config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> None:
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

    def record(self) -> tp.Generator:
        """
        unit_uuid: UUID of a unit passport associated with a unit, which assembly
        process is being recorded by the camera

        main method to record video from camera. Uses popen and ffmpeg utility

        :returns: saved video relative path
        """

        # setup a coroutine
        while True:
            # receive UUID
            try:
                unit_uuid: str = yield
            except StopIteration:
                logging.info("Killed the Camera coroutine")

            # new video filepath. It is to be saved in a separate directory
            # with a UUID and number in case a unit has more than one video associated with it
            filename = f"output/unit_{unit_uuid}_assembly_video_1.mp4"

            # determine a valid video name not to override an existing video
            cnt = 1
            while path.exists(filename):
                filename.replace(f"video_{cnt}", f"video_{cnt + 1}")
                cnt += 1

            program_ffmpeg = (
                    'ffmpeg -rtsp_transport tcp -i "rtsp://'  # using rtsp to get stream
                    + self.login
                    + ":"
                    + self.password
                    + "@"
                    + self.ip
                    + ":"
                    + self.port
                    + '/Streaming/Channels/101" -r 25 -c copy -map 0 '
                    + filename
            )  # the entire line looks like
            # ffmpeg -rtsp_transport tcp -i "rtsp://login:password@ip:port/Streaming/Channels/101" -c copy -map 0 vid.mp4
            # more on ffmpeg.org
            process_ffmpeg = subprocess.Popen(
                "exec " + program_ffmpeg,
                shell=True,  # execute in shell
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,  # to get access to all the flows
            )
            logging.info(f"Started recording video '{filename}'")

            # record is started in a subprocess and function can give up it's context control
            # for now in order to avoid hanging up the thread. next call of the function (which is now a generator)
            # will result in the execution of the code which is following after yield keyword until it reaches next one
            yield

            logging.info(f"Finished recording video '{filename}'")
            time.sleep(1)  # some time to finish the process
            process_ffmpeg.kill()  # kill the subprocess to liberate system resources

            yield filename
