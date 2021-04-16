import logging

from PIL import Image
from brother_ql import BrotherQLRaster, conversion
from brother_ql.backends.helpers import send


class Task:
    def __init__(self, picname: str) -> None:
        """
        :param picname: path to a picture to be printed
        :type picname: str

        When creating an instance of the class, it creates a task for a brother QL-800 printer to print a label with a
        qr-code passed as an argument. picname != qrpic, it contains side fields and logos (optionally)
        """
        logging.warning("Initializing printer")

        qr = Image.open(picname)

        printer = "usb://0x04f9:0x209b"  # link to device on RPI
        label_name = "62"  # that depends on paper used for printing

        logging.warning("Printing...")
        qlr = BrotherQLRaster("QL-800")
        conversion.convert(qlr, [qr], label_name, red=True)
        send(qlr.data, printer)  # this is some standard code for printing with brother label printer with python,
        # red = True means that black and red printing will be done. Only for 62 label paper
        logging.warning("Printed!")
