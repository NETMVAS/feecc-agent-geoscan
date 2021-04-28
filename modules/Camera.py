import logging
import subprocess
import time
from os import path
import typing as tp

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
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
        self.recording_ongoing: bool = False  # current status
        self.process_ffmpeg = None  # popen object o ffmpeg subprocess

    def start_record(self, unit_uuid: str) -> str:
        """
        unit_uuid: UUID of a unit passport associated with a unit, which assembly
        process is being recorded by the camera

        main method to record video from camera. Uses popen and ffmpeg utility

        :returns: saved video relative path
        """

        # new video filepath. It is to be saved in a separate directory
        # with a UUID and number in case a unit has more than one video associated with it
        filename = f"output/unit_{unit_uuid}_assembly_video_1.mp4"

        # determine a valid video name not to override an existing video
        cnt = 1
        while path.exists(filename):
            filename.replace(f"video_{cnt}", f"video_{cnt + 1}")
            cnt += 1

        program_ffmpeg = \
            f'ffmpeg -rtsp_transport tcp -i "rtsp://{self.login}:{self.password}@{self.ip}:{self.port}\
/Streaming/Channels/101" -r 25 -c copy -map 0 {filename}'
        # the entire line looks like
        # ffmpeg -rtsp_transport tcp -i "rtsp://login:password@ip:port/Streaming/Channels/101" -c copy -map 0 vid.mp4
        # more on ffmpeg.org
        self.process_ffmpeg = subprocess.Popen(
            "exec " + program_ffmpeg,
            shell=True,  # execute in shell
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,  # to get access to all the flows
        )
        logging.info(f"Started recording video '{filename}'")

        self.recording_ongoing = True

        return filename

    def stop_record(self) -> None:
        """stop recording a video"""

        if self.process_ffmpeg and self.recording_ongoing:
            self.process_ffmpeg.terminate()  # kill the subprocess to liberate system resources
            logging.info(f"Finished recording video")
            self.recording_ongoing = False
            time.sleep(1)  # some time to finish the process
