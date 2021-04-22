import requests
import logging

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Agent:
    """Handles agent's state management and high level operation"""

    def __init__(self):
        """agent is initialized with state 0"""

        self.state: int = 0
        self.backend_api_address: str = ''

    def state_0(self) -> None:
        """at state 0 agent awaits for an incoming RFID event and is practically sleeping"""

        pass

    def state_1(self) -> None:
        """at state 1 agent awaits for an incoming RFID event OR form post, thus operation is
        primarily done in app.py handlers, sleeping"""

        pass

    # todo
    def state_2(self) -> None:
        """
        at state 2 agent is recording the work process using an IP camera and awaits an
        RFID event which would stop the recording
        """

        # start the recording in the background
        pass

    # todo
    def state_3(self) -> None:
        """
        then the agent receives an RFID event, recording is stopped and published to IPFS.
        Passport is dumped and also published into IPFS, it's checksum is stored in Robonomics.
        A short link is generated for the video and gets encoded in a QR code, which is printed on a sticker.
        When everything is done, background pinning of the files is started, own state is changed to 0.
        """

        # stop recording and save the file
        pass

        # publish video into IPFS
        pass

        # generate a video short link
        pass

        # generate a QR code with the short link
        pass

        # print the QR code onto a sticker
        pass

        # set up a background pin operation to Pinata
        pass

        # change own state back to 0
        self.state = 0

    def run(self) -> None:
        """monitor own state and switch modes according to it's change"""

        # note latest known state
        latest_state: int = self.state

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

                # sync backend state with the own one
                self._update_backend_state(priority=1)

                # update latest known state
                latest_state = self.state

    def _update_backend_state(self, priority: int) -> None:
        """post an updated system state to the backend to keep it synced with the local state"""

        logging.info(f"Changing backend state to {self.state}")
        change_backend_state = requests.post(
            url=f"{self.backend_api_address}/state-update",
            json={
                "change_state_to": self.state,
                "priority": priority
            }
        )

        if change_backend_state.ok:
            logging.info(f"Send backend state transition request: success")
        else:
            logging.error(f"backend state transition request failed: HTTP code {change_backend_state.status_code}")
