import requests
import logging
from time import sleep
import typing as tp
from sys import exit

from modules.Camera import Camera
import modules.Printer as Printer
import modules.send_to_ipfs as ipfs
import modules.url_generator as url_generator
import modules.qr_generator as qr_generator
from Passport import Passport

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Agent:
    """Handles agent's state management and high level operation"""

    def __init__(self, config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> None:
        """agent is initialized with state 0 and has an instance of Passport and Camera associated with it"""

        self.state: int = 0
        self.config: tp.Dict[str, tp.Dict[str, tp.Any]] = config
        self.backend_api_address: str = config["api_address"]["backend_api_address"]
        self.associated_passport: tp.Optional[Passport] = None
        self.associated_camera: Camera = Camera(self.config)
        self.latest_record_filename: str = ""
        self.latest_record_short_link: str = ""
        self.latest_record_qrpic_filename: str = ""

    def state_0(self) -> None:
        """at state 0 agent awaits for an incoming RFID event and is practically sleeping"""

        pass

    def state_1(self) -> None:
        """at state 1 agent awaits for an incoming RFID event OR form post, thus operation is
        primarily done in app.py handlers, sleeping"""

        pass

    def state_2(self) -> None:
        """
        at state 2 agent is recording the work process using an IP camera and awaits an
        RFID event which would stop the recording
        """

        # start the recording in the background and send the path to the video
        try:
            passport_id = self.associated_passport.passport_id
        except AttributeError as E:
            logging.error(
                f"Failed to start video recording: error retrieving associated passport ID.\n\
                self.associated_passport = {self.associated_passport}\n{E}")
            exit()

        self.latest_record_filename = self.associated_camera.start_record(passport_id)

    def state_3(self) -> None:
        """
        then the agent receives an RFID event, recording is stopped and published to IPFS.
        Passport is dumped and also published into IPFS, it's checksum is stored in Robonomics.
        A short link is generated for the video and gets encoded in a QR code, which is printed on a sticker.
        When everything is done, background pinning of the files is started, own state is changed to 0.
        """

        # stop recording and save the file
        self.associated_camera.stop_record()

        # generate a video short link (a dummy for now)
        self.latest_record_short_link = url_generator.create_url(self.config)[1]

        # generate a QR code with the short link
        self.latest_record_qrpic_filename = qr_generator.create_qr(
            link=self.latest_record_short_link,
            config=self.config
        )

        # print the QR code onto a sticker if set to do so in the config
        if self.config["print_qr"]["enable"]:
            Printer.Task(
                picname=self.latest_record_qrpic_filename,
                config=self.config
            )

        # publish video into IPFS and pin to Pinata
        # update the short link to point to an actual recording
        ipfs.send(
            filename=self.latest_record_filename,
            qrpic=self.latest_record_qrpic_filename,
            config=self.config,
            keyword=self.latest_record_short_link.split('/')[-1]
        )

        # save th passport into a file
        self.associated_passport.export_yaml()

        # change own state back to 0
        self.state = 0

    def run(self) -> None:
        """monitor own state and switch modes according to it's change"""

        # note latest known state
        latest_state: int = -1

        # monitor own state change
        while True:  # to be replaced with asyncio
            # detect change of the state
            if latest_state != self.state:

                # do state related actions when state switch detected
                if self.state == 0:
                    self.state_0()

                elif self.state == 1:
                    self.state_1()

                elif self.state == 2:
                    self.state_2()

                elif self.state == 3:
                    self.state_3()

                # report own state transition
                logging.info(f"Agent state is now {self.state}")

                # sync backend state with the own one
                self._update_backend_state(priority=1)

                # update latest known state
                latest_state = self.state

            # sleep before next update
            sleep(0.2)

    def _update_backend_state(self, priority: int) -> None:
        """post an updated system state to the backend to keep it synced with the local state"""

        logging.info(f"Changing backend state to {self.state}")

        logging.debug(f"self.backend_api_address = {self.backend_api_address}")

        target_url = f"{self.backend_api_address}/state-update"
        payload = {
                "change_state_to": self.state,
                "priority": priority
            }

        logging.debug(f"Sending request to:\n {target_url}\nWith payload:\n{payload}")

        change_backend_state = requests.post(
            url=target_url,
            json=payload
        )

        if change_backend_state.status_code == 200:
            logging.info(f"Send backend state transition request: success")
        else:
            logging.error(f"backend state transition request failed: HTTP code {change_backend_state.status_code}")
