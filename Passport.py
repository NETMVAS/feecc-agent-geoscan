import logging
import typing as tp
import uuid
import csv
import yaml
import hashlib
from datetime import datetime as dt
import os
import modules.send_to_ipfs as ipfs

# set up logging
logging.basicConfig(
    level=logging.INFO,
    filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Passport:
    """handles form validation and unit passport issuing"""

    def __init__(self, rfid_card_id: str, config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> None:
        # passport id and employee data based on employee ID
        self.passport_id: str = uuid.uuid4().hex
        self.passport_ipfs_hash: str = ""
        self.config = config
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
        self.filename: str = ""

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
            "production_stage": "Final assembly",
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
            self.session_start_time = form["session_start_time"]
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
        employee_passport_code = hashlib.sha256(employee_passport_string_encoded).hexdigest()

        logging.debug(f"self.session_start_time = {self.session_start_time}")

        passport_dict = {
            "Уникальный номер паспорта изделия": self.passport_id,
            "Модель изделия": self.product_type,
            "Комплектация": self.additional_info,
            "Начало сборки": self.session_start_time,
            "Окончание сборки": self.session_end_time,
            "Этап производства": self.workplace_data,
            "Изготовил": employee_passport_code,
            "Видеозаписи процесса сборки в IPFS": self.video_ipfs_hash
        }

        logging.debug(f"raw passport_dict = {passport_dict}")

        # make directory if it is missing
        if not os.path.isdir("unit-passports"):
            os.mkdir("unit-passports")

        # save into a file and save the filename
        self.filename = f"unit-passports/unit-passport-{self.passport_id}.yaml"
        with open(self.filename, "w") as passport_file:
            yaml.dump(
                passport_dict,
                passport_file,
                allow_unicode=True,
                sort_keys=False
            )

        logging.info(f"Unit passport with UUID {self.passport_id} has been dumped successfully")

        # upload passport file into IPFS and pin it to Pinata, publish hash to Robonomics
        self.passport_ipfs_hash = ipfs.send(
            filename=self.filename,
            config=self.config
        )

        # also save passport IPFS hash locally in case Robonomics datalog is not written
        with open("issued_passports.csv", "a") as file:
            file.writelines(
                f"{self.passport_id};{self.passport_ipfs_hash}\n"
            )

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

        for _hash in ipfs_hash:
            self.video_ipfs_hash.append(_hash)

        self.session_end_time = dt.now().strftime("%d-%m-%Y %H:%M:%S")
