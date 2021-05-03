import logging
import typing as tp
from PIL import Image
from brother_ql import BrotherQLRaster, conversion
from brother_ql.backends.helpers import send

# set up logging
logging.basicConfig(
    level=logging.INFO,
    filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Task:
    def __init__(self, picname: str, config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> None:
        """
        :param picname: path to a picture to be printed
        :type picname: str

        When creating an instance of the class, it creates a task for a brother QL-800 printer to print a label with a
        qr-code passed as an argument. picname != qrpic, it contains side fields and logos (optionally)
        """

        logging.info("Initializing printer")

        qr = Image.open(picname)
        printer_config: tp.Dict[str, tp.Any] = config["printer"]
        printer: str = printer_config["address"]  # link to device
        label_name = str(printer_config["paper_width"])  # that depends on paper used for printing

        logging.info("Printing...")
        qlr = BrotherQLRaster(printer_config["printer_model"])
        red: bool = (label_name == "62")
        conversion.convert(qlr, [qr], label_name, red=red)
        send(qlr.data, printer)  # this is some standard code for printing with brother label printer with python,
        # red = True means that black and red printing will be done. Only for 62 label paper
        logging.info("Printed!")
