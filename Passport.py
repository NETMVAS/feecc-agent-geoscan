import logging
import typing as tp
import uuid
import csv
import yaml
import hashlib
from datetime import datetime as dt

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Passport:
    """handles form validation and unit passport issuing"""

    def __init__(self, rfid_card_id: str) -> None:
        # passport id and employee data based on employee ID
        self.passport_id: str = uuid.uuid4().hex
        self._employee_id: str = rfid_card_id
        self._employee_db_entry: tp.List[str] = self._find_in_db()

        # refuse service if employee unknown
        if not self._employee_db_entry:
            logging.error(f"Employee with ID {self._employee_id} is not in the DB, service refused")
            raise ValueError

        # refuse service if employee database has wrong format
        valid_len = 3
        if not len(self._employee_db_entry) == 3:
            logging.critical(f"Employee DB has to have at least {valid_len} columns")
            return

        # log success
        logging.info(f"Passport {self.passport_id} initialized by employee with ID {self._employee_id}")

        # passport field
        self.employee_name: str = self._employee_db_entry[1]
        self.employee_position: str = self._employee_db_entry[2]
        self.session_start_time: str = ""
        self.session_end_time: str = ""
        self.workplace_data: str = ""
        self.product_type: str = ""
        self.additional_info: tp.Dict[str, str] = {}
        self.video_ipfs_hash: tp.List[str] = []

    def submit_form(self, form: tp.Dict[str, tp.Any]) -> bool:
        """
        accepts a JSON form, validates it and assigns
        form contents to instance's properties if form is valid (returns True).
        If validation failed - returns False and does nothing.
        """

        # validate form
        reference_form = {
            "session_start_time": "01-01-1970 00:00:00",
            "product_type": "Perseverance Mars rover",
            # "production_stage": "Final assembly",
            "additional_info":
                {
                    "field_1": "Sample text",
                    "field_2": "Sample text",
                    "field_3": "Sample text"
                }
        }

        form_keys = list(form.keys())
        form_keys.sort()
        reference_form_keys = list(reference_form.keys())
        reference_form_keys.sort()

        if form_keys == reference_form_keys:
            # convert timestamp
            session_start_time = dt.strptime(
                date_string=form["session_start_time"],
                format="%-m/%-d/%Y, %H:%M:%S %p"
            )

            session_start_time = dt.strftime(
                fmt="%d-%m-%Y %H-%M-%S"
            )

            self.session_start_time = session_start_time
            self.product_type = form["product_type"]
            self.additional_info = form["additional_info"]
            self.workplace_data = form["production_stage"]

            return True

        else:
            logging.error(f"Error validating form data. Key mismatch with reference model")
            return False

    def export_yaml(self) -> None:
        """makes a unit passport and dumps it in a form of a YAML file"""

        # since unit passport will be published to IPFS, employee name is replaced with
        # "employee passport code" - an SHA256 checksum of a string, which is a space-separated
        # combination of employee's ID, name and position. since this data is unique for every
        # employee, it is safe to assume, that collision is impossible.

        # generate employee passport code
        employee_passport_string = " ".join(self._employee_db_entry)
        employee_passport_string_encoded = employee_passport_string.encode()
        employee_passport_code = hashlib.sha256(employee_passport_string_encoded)

        passport_dict = {
            "Уникальный номер паспорта изделия": self.passport_id,
            "Модель изделия": self.product_type,
            "Доп. информация": self.additional_info,
            "Начало сборки": self.session_start_time,
            "Окончание сборки": self.session_end_time,
            "Рабочее место": self.workplace_data,
            "Изготовил": employee_passport_code,
            "Видеозаписи процесса сборки в IPFS": self.video_ipfs_hash
        }

        # save into a file
        with open(f"unit-passports/unit-passport-{self.passport_id}.yaml", "w") as passport_file:
            yaml.dump(passport_dict, passport_file)

        logging.info(f"Unit passport with UUID {self.passport_id} has been dumped successfully")

    def _find_in_db(self) -> tp.List[str]:
        """:returns employee data, incl. name, position and employee ID if employee found in DB"""

        employee_data = []

        # open employee database
        employee_db = "employee_db.csv"

        try:
            with open(employee_db, "r") as file:
                reader = csv.reader(file)

                # look for employee in the db
                for row in reader:
                    if self._employee_id in row:
                        employee_data = row
                        break
        except FileNotFoundError:
            logging.critical(f"File '{employee_db}' is not in the working directory, cannot retrieve employee data")

        return employee_data

    def end_session(self, ipfs_hash: tp.List[str]) -> None:
        """wrap up the session when video recording stops an save video data as well as session end timestamp"""

        self.video_ipfs_hash += ipfs_hash
        self.session_end_time = dt.now().strftime("%d-%m-%Y %H-%M-%S")
