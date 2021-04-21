import logging
import typing as tp
import uuid

import yaml

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Passport:
    """handles form validation and unit passport issuing"""

    def __init__(self) -> None:
        # passport id
        self.passport_id: str = uuid.uuid4().hex
        logging.info(f"Passport {self.passport_id} initialized")

        # passport field
        self.employee_name: str = ""
        self.session_start_time: str = ""
        self.session_end_time: str = ""
        self.workplace_data: str = "Рабочее место №1"
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

            return True
        else:
            logging.error(f"Error validating form data. Key mismatch with reference model")
            return False

    def export_yaml(self) -> None:
        """makes a unit passport and dumps it in a form of a YAML file"""

        passport_dict = {
            "Уникальный номер паспорта изделия": self.passport_id,
            "Модель изделия": self.product_type,
            "Доп. информация": self.additional_info,
            "Начало сборки": self.session_start_time,
            "Окончание сборки": self.session_end_time,
            "Рабочее место": self.workplace_data,
            "Изготовил": self.employee_name,
            "Видеозаписи процесса сборки в IPFS": self.video_ipfs_hash
        }

        # save into a file
        with open(f"unit-passports/unit-passport-{self.passport_id}.yaml", "w") as passport_file:
            yaml.dump(passport_dict, passport_file)
