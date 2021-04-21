from flask import Flask, request, Response
from flask_restful import Api, Resource
import typing as tp
import requests
import logging

from Agent import Agent
from Passport import Passport

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)

logging.info('Agent API listener started')

# global variables
backend_api_address: str = "http://127.0.0.1:5000/api"
valid_states = [0, 1, 2, 3]

# instantiate objects
agent = Agent()
app = Flask(__name__)
api = Api(app)


def update_backend_state(priority: int) -> int:
    """post an updated system state to the backend to keep it synced with the local state"""

    logging.info(f"Changing backend state to {agent.state}")
    change_backend_state = requests.post(
        url=f"{backend_api_address}/state-update",
        json={
            "change_state_to": agent.state,
            "priority": priority
        }
    )

    return change_backend_state.status_code


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
        passport = Passport()


        # todo
        # validate the form and change own state
        if passport.submit_form(form_data):
            agent.state = 2
            update_backend_state(priority=1)

            logging.info(
                f"Form validation success. Current state: {agent.state}"
            )

        else:
            logging.error(
                f"""
                Invalid form 
                Form: {form_data}
                Current state: {agent.state}
                """
            )

        return 200


class StateUpdateHandler(Resource):
    """handles a state update request"""

    def post(self) -> int:
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


# todo
class RFIDHandler(Resource):
    """handles RFID scanner events"""

    def post(self) -> int:
        pass


# REST API endpoints
api.add_resource(FormHandler, "/api/form-handler")
api.add_resource(StateUpdateHandler, "/api/state-update")
api.add_resource(RFIDHandler, "/api/rfid")

if __name__ == "__main__":
    agent.run()
    app.run(host="0.0.0.0", port=8080)
