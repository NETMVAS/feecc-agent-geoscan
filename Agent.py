# todo
class Agent:
    """Handles agent's state management and high level operation"""

    def __init__(self):
        self.state: int = 0

    def state_0(self):
        pass

    def state_1(self):
        pass

    def state_2(self):
        pass

    def state_3(self):
        pass

    def run(self):
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

                # update latest known state
                latest_state = self.state
