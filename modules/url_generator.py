import ast
import logging
import requests

import typing as tp

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


def create_url(config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> tp.Tuple[tp.Any, tp.Any]:
    """
    :param config: dictionary containing all the configurations
    :type config: dict
    :return keyword: shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
    :return link: full yourls url. E.g. url.today/6b

    create an url to redirecting service to encode it in the qr and print. Redirecting to some dummy link initially
    just to print the qr, later the redirect link is updated with a gateway link to the video
    """
    try:
        url = "https://" + config["yourls"]["server"] + "/yourls-api.php"
        querystring = {
            "username": config["yourls"]["username"],
            "password": config["yourls"]["password"],
            "action": "shorturl",
            "format": "json",
            "url": config["ipfs"]["gateway_address"],
        }  # api call to the yourls server. More on yourls.org
        payload = ""  # payload. Server creates a short url and returns it as a response
        response = requests.request("GET", url, data=payload, params=querystring)  # get the created url keyword.

        logging.debug(response.text)
        keyword = ast.literal_eval(response._content.decode("utf-8"))["url"]["keyword"]
        link = config["yourls"]["server"] + "/" + keyword  # link of form url.today/6b
        return keyword, link
    except Exception as e:
        logging.error("Failed to create URL, replaced by url.today/55. Error: ", e)
        return "55", "url.today/55"  # time to time creating url fails. To go on just set a dummy url and keyword


def update_url(keyword: str, ipfs_hash: str, config: tp.Dict[str, tp.Dict[str, tp.Any]]) -> None:
    """
    :param keyword: shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
    :type keyword: str
    :param ipfs_hash: IPFS hash of a recorded video
    :type ipfs_hash: str
    :param config: dictionary containing all the configurations
    :type config: dict

    Update redirecting service so that now the short url leads to gateway to a video in ipfs
    """
    try:
        url = "https://" + config["yourls"]["server"] + "/yourls-api.php"
        querystring = {
            "username": config["yourls"]["username"],
            "password": config["yourls"]["password"],
            "action": "update",
            "format": "json",
            "url": config["ipfs"]["gateway_address"] + ipfs_hash,
            "shorturl": keyword,
        }
        payload = ""  # another api call with no payload just to update the link. More on yourls.org. Call created with
        # insomnia
        response = requests.request("GET", url, data=payload, params=querystring)
        # no need to read the response. Just wait till the process finishes
        logging.debug(response)
    except Exception as e:
        logging.warning("Failed to update URL: ", e)
