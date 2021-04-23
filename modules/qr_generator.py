import qrcode
import time

from PIL import Image, ImageOps


def create_qr(link: str, config: dict) -> str:
    """
    :param link: full yourls url. E.g. url.today/6b
    :type link: str
    :param config: dictionary containing all the configurations
    :type config: dict
    :return: full filename of a resulted qr-code
    :rtype: str

    This is a qr-creating submodule. Inserts a robonomics logo inside the qr and adds logos aside if required
    """
    inpic_s = 100  # size of robonomics logo in pixels
    robonomics = Image.open("media/robonomics.jpg").resize(
        (inpic_s, inpic_s)  # resize logo if it's not the demanded size
    )
    qr_big = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr_big.add_data("https://" + link)
    qr_big.make()
    img_qr_big = qr_big.make_image().convert("RGB")  # some standard code to create qr-code with a python lib

    pos = (
        (img_qr_big.size[0] - robonomics.size[0]) // 2,
        (img_qr_big.size[1] - robonomics.size[1]) // 2,
    )  # position to insert to logo right in the center of a qr-code

    qr_s = 200  # size of the entire qr-code
    border_s = int((696 - qr_s) / 2)  # 696 comes from a brother_ql label size accordance. Label of 62 mm corresponds to
    # 696 pixels picture size
    img_qr_big.paste(robonomics, pos)  # insert logo
    img_qr_big = img_qr_big.resize((qr_s, qr_s))  # resize qr
    img_qr_big = ImageOps.expand(img_qr_big, border=border_s, fill="white")  # add borders. it makes a square picture
    left, top, right, bottom = 0, border_s - 2, qr_s + border_s * 2, border_s + qr_s + 2
    img_qr_big = img_qr_big.crop((left, top, right, bottom))  # crop top and bottom borders to make image rectangular

    if config["print_qr"]["logos"]:
        left_pic = Image.open("media/left_pic.jpg").resize((qr_s, qr_s))
        posl = (24, 2)
        img_qr_big.paste(left_pic, posl)

        right_pic = Image.open("media/right_pic.jpg").resize((qr_s, qr_s))
        posr = (696 - qr_s - 24, 2)
        img_qr_big.paste(right_pic, posr)
    # this is used to paste logos if needed. Position is set empirically so that logos are aside of the qr-code
    qrpic = "output/" + time.ctime(time.time()).replace(" ", "_") + "qr.png"
    img_qr_big.save(qrpic)  # saving picture for further printing with a timestamp

    return qrpic
