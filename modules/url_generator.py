import ast
import logging
import requests

from typing import Tuple, Any


def create_url(config: dict) -> Tuple[Any, Any]:
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
            "url": "http://gateway.ipfs.io",
        }  # api call to the yourls server. More on yourls.org
        payload = ""  # payload. Server creates a short url and returns it as a response
        response = requests.request("GET", url, data=payload, params=querystring)  # get the created url keyword.

        logging.debug(response.text)
        keyword = ast.literal_eval(response._content.decode("utf-8"))["url"]["keyword"]
        link = config["yourls"]["server"] + "/" + keyword  # link of form url.today/6b
        return keyword, link
    except Exception as e:
        logging.warning("Failed to create URL, replaced by url.today/55. Error: ", e)
        return "55", "url.today/55"  # time to time creating url fails. To go on just set a dummy url and keyword


def update_url(keyword: str, hash: str, config: dict) -> None:
    """
    :param keyword: shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
    :type keyword: str
    :param hash: IPFS hash of a recorded video
    :type hash: str
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
            "url": "http://gateway.ipfs.io/ipfs/" + hash,
            "shorturl": keyword,
        }
        payload = ""  # another api call with no payload just to update the link. More on yourls.org. Call created with
        # insomnia
        response = requests.request("GET", url, data=payload, params=querystring)
        # no need to read the response. Just wait till the process finishes
        logging.debug(response)
    except Exception as e:
        logging.warning("Failed to update URL: ", e)
