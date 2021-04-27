from flask import Flask, request, Response
from flask_restful import Api, Resource
import typing as tp
import logging
import yaml
from sys import exit
import threading

from Agent import Agent
from Passport import Passport

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


def read_configuration() -> tp.Dict[str, tp.Dict[str, tp.Any]]:
    """
    :return: dictionary containing all the configurations
    :rtype: dict

    Reading config, containing all the required data, such as filepath, robonomics parameters (remote wss, seed),
    camera parameters (ip, login, password, port), etc
    """
    config_path = "config/config.yaml"
    logging.debug(f"Looking for config in {config_path}")

    try:
        with open(config_path) as f:
            content = f.read()
            config_f: tp.Dict[str, tp.Dict[str, tp.Any]] = yaml.load(content, Loader=yaml.FullLoader)
            logging.debug(f"Configuration dict: {content}")
            return config_f
    except Exception as e:
        while True:
            logging.error("Error in configuration file!")
            logging.error(e)
            exit()


logging.info('Agent API listener started')

# global variables
backend_api_address: str = "http://127.0.0.1:8080/api"
valid_states = [0, 1, 2, 3]
config: tp.Dict[str, tp.Dict[str, tp.Any]] = read_configuration()

# instantiate objects
passport = Passport("0008368511")
agent = Agent(config=config)
agent_thread = threading.Thread(target=agent.run)
agent.backend_api_address = backend_api_address
app = Flask(__name__)
api = Api(app)


# REST API request handlers
class FormHandler(Resource):
    """accepts a filled form from the backend and uses it to form a unit passport"""

    def post(self) -> int:
        logging.info(
            f"Received a form. Parsing and validating"
        )

        # parse the form data
        form_data = request.get_json()

        global agent
        global passport

        # validate the form and change own state
        if passport.submit_form(form_data):
            agent.associated_passport = passport
            agent.state = 2

            logging.info(
                f"Form validation success. Current state: {agent.state}"
            )

        else:
            agent.state = 0

            logging.error(
                f"""
                Invalid form, state reset to 0
                Form: {form_data}
                Current state: {agent.state}
                """
            )

        return 200


class StateUpdateHandler(Resource):
    """handles a state update request"""

    def post(self):
        logging.info(
            f"Received a request to update the state."
        )

        # parse the request data
        data = request.get_json()

        # validate the request
        global valid_states
        global agent

        if not data["change_state_to"] in valid_states:
            logging.warning(
                f"Invalid state transition: '{data['change_state_to']}' is not a valid state. Staying at {agent.state}"
            )

            return Response(
                response='{"status": 406, "msg": "invalid state"}',
                status=406
            )

        # change own state to the one specified by the sender
        agent.state = data["change_state_to"]

        logging.info(
            f"Successful state transition to {data['change_state_to']}"
        )

        return 200


class RFIDHandler(Resource):
    """handles RFID scanner events"""

    def post(self) -> int:

        # parse RFID card ID from the request
        card_id = request.get_json()["string"]

        # log the event
        logging.info(f"read RFID card with ID {card_id}")

        # start session
        if agent.state == 0:

            # create a passport for the provided employee
            try:
                global passport
                passport = Passport(card_id)
                agent.state = 1

            except ValueError:
                logging.info(f"Passport creation failed, staying at state 0")

        # cancel session
        elif agent.state == 1:
            agent.state = 0

        # end session
        elif agent.state == 2:
            agent.state = 3

        # ignore interaction when in state 3
        else:
            pass

        return 200


# REST API endpoints
api.add_resource(FormHandler, "/api/form-handler")
api.add_resource(StateUpdateHandler, "/api/state-update")
api.add_resource(RFIDHandler, "/api/rfid")

if __name__ == "__main__":
    agent_thread.start()
    app.run(host="127.0.0.1", port=5000)
    agent_thread.join()
