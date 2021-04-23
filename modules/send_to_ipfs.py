import ipfshttpclient
import logging
import os
import subprocess


from pinatapy import PinataPy
from modules.url_generator import update_url

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    # filename="agent.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)


class Error(Exception):
    pass


def concatenate(dirname: str, filename: str) -> str:
    """
    :param dirname: path to the project ending with .../cameras_robonomics
    :type dirname: str
    :param filename: full name of a recorded video
    :type filename: str
    :return: full name of a new video (concatenated with intro)
    :rtype: str

    concatenating two videos (intro with a main video) if needed. Intro is to be placed in media folder. More in config
    file
    """
    logging.info("Concatenating videos")
    if not os.path.exists(dirname + "/media/intro.mp4"):
        raise Error("Intro file doesn't exist!")
    concat_string = "file \'" + dirname + "/media/intro.mp4\'\nfile \'" + filename + "\'"
    # it should look like:
    #   file './media/intro.mp4'
    #   file './media/vid.mp4'
    with open(dirname + "/output/vidlist.txt", "w") as text_file:
        text_file.write(concat_string)
        text_file.close()  # create txt file
    concat_filename = filename[:-4] + "_intro" + filename[-4:]  # new file will have another name to detect concatenated
    # videos
    concat_command = (
        "ffmpeg -f concat -safe 0 -i "
        + dirname
        + "/output/vidlist.txt -c copy "
        + concat_filename
    )  # line looks like: ffmpeg -f concat -safe 0 -i vidlist.txt -c copy output.mp4. More on ffmpeg.org
    concat_process = subprocess.Popen(
        "exec " + concat_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )  # subprocess to execute ffmpeg utility command in shell and obtain all the flows
    concat_process.stdout.readline()  # wait till the process finishes
    return concat_filename  # return new filename


def _pin_to_pinata(filename: str, config: dict) -> None:
    """
    :param filename: full name of a recorded video
    :type filename: str
    :param config: dictionary containing all the configurations
    :type config: dict

    pinning files in pinata to make them broadcasted around ipfs
    """
    pinata_api = config["pinata"]["pinata_api"]  # pinata credentials
    pinata_secret_api = config["pinata"]["pinata_secret_api"]
    if pinata_api and pinata_secret_api:
        pinata = PinataPy(pinata_api, pinata_secret_api)
        pinata.pin_file_to_ipfs(filename)  # here we actually send the entire file to pinata, not just its hash. It will
        # remain the same as if published locally, cause the content is the same.
        logging.info("File sent")


def send(filename: str, keyword: str, qrpic: str, config: dict) -> None:
    """
    :param filename: full name of a recorded video
    :type filename: str
    :param keyword: shorturl keyword. More on yourls.org. E.g. url.today/6b. 6b is a keyword
    :type keyword: str
    :param qrpic: name of a qr-code file. Qr-code, which is redirecting to IPFS gateway
    :type qrpic: str
    :param config: dictionary containing all the configurations
    :type config: dict

    concatenate if needed, publish files to ipfs locally, send them to pinata, push hashes to robonomics
    """
    if config["intro"]["enable"]:
        try:
            non_concatenated_filename = filename  # save old filename to delete if later
            filename = filename  # get concatenated video filename
        except Exception as e:
            logging.error("Failed to concatenate. Error: ", e)

    if config["ipfs"]["enable"]:
        try:
            client = ipfshttpclient.connect()  # establish connection to local ipfs node
            res = client.add(filename)  # publish vide locally
            ipfs_hash = res["Hash"]  # get its hash of form Qm....
            logging.info("Published to IPFS, hash: " + ipfs_hash)
            update_url(keyword, ipfs_hash, config)  # after publishing file in ipfs locally, which is pretty fast,
            # update the link on the qr code so that it redirects now to the gateway with a published file. It may
            # take some for the gateway node to find the file, so we need to pin it in pinata
            if config["pinata"]["enable"]:
                logging.info("Camera is sending file to Pinata")
                _pin_to_pinata(filename, config)  # pin file in pinata if needed
            logging.info("Updating URL")

        except Exception as e:
            logging.error(
                "Error while publishing to IPFS or pinning to pinata. Error: ", e
            )

    if config["general"]["delete_after_record"]:
        try:
            logging.info("Removing files")
            os.remove(filename)
            os.remove(qrpic)
            if config["intro"]["enable"]:
                os.remove(non_concatenated_filename)  # liberate free space. delete both concatenated and initial files
        except Exception as e:
            logging.error("Error while deleting file, error: ", e)

    if config["datalog"]["enable"] and config["ipfs"]["enable"]:
        try:
            program = (
                'echo \"' + ipfs_hash + '\" | '  # send ipfs hash
                + config["transaction"]["path_to_robonomics_file"] + " io write datalog "  # to robonomics chain
                + config["transaction"]["remote"]  # specify remote wss, if calling remote node
                + " -s "
                + config["camera"]["key"]  # sing transaction with camera seed
            )  # line of form  echo "Qm…" | ./robonomics io write datalog -s seed. See robonomics wiki for more
            process = subprocess.Popen(program, shell=True, stdout=subprocess.PIPE)
            output = process.stdout.readline()  # execute the command in shell and wait for it to complete
            logging.info(
                "Published data to chain. Transaction hash is "
                + output.strip().decode("utf8")
            )  # get transaction hash to use it further if needed
        except Exception as e:
            logging.error("Error while sending IPFS hash to chain, error: ", e)
