from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time

import logging
logging.basicConfig(format='[%(asctime)s \t%(filename)s \t %(funcName)s] -\t%(message)s', level=logging.WARNING)

import sys, os
from pathlib import Path

import argparse

parser = argparse.ArgumentParser(description="Fully functional WhatsApp Web bot with AI text generation.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# Arguments
parser.add_argument("--gpt_folder_name", type=str, default="gpt-2-finetuning", help="Name of the gpt-2 folder")
parser.add_argument("--url", type=str, default="https://web.whatsapp.com/", help="WhatsApp Web URL")
parser.add_argument("--group", type=str, default="Gappi", help="Name of the 'group' for the bot to reply")
parser.add_argument("--identifier", type=str, default="not_mirani_bot", help="Identifier found in a message triggers a reply")
parser.add_argument("--periodicity", type=int, default=5, help="Amount of time (in secs) the program waits to go check for new messages")
parser.add_argument("--cred_file", type=str, default="cred.txt", help="Name of the file containing browser credentials")

args = parser.parse_args()

gpt_path = os.path.join(Path.cwd().parent, "{}/src".format(args.gpt_folder_name))
sys.path.insert(1, gpt_path)
from auto_reply_msg import interact_model as reply


# Launch a new Chrome browser window to get driver object, then
# either switch it to existing window or return new window handle
def launchChrome(remote=False,
                 executor_url=None,
                 session_id=None):
    if remote:
        logging.info("Trying to resumes an existing browser session")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Remote(
            command_executor=executor_url,
            desired_capabilities=chrome_options.to_capabilities())
        driver.session_id = session_id
    else:
        logging.info("Opening new browser window")
        driver = webdriver.Chrome()

    return driver


# Get new credentials from newly opened file and write it in cred.txt
def get_new_credentials():
    driver = launchChrome()
    logging.info("New browser window opened")
    executor_url = driver.command_executor._url
    session_id = driver.session_id
    logging.info("Setting new credentials in 'cred.txt' file")
    with open(args.cred_file, "w") as f:
        f.write("session_id {}\n".format(session_id))
        f.write("executor_url {}".format(executor_url))

    return (driver)


# Get driver, either from an existing Chrome window or a new one
def get_driver():
    try:
        logging.info("Trying to open cred.txt file to fetch existing credentials")
        with open(args.cred_file, "r") as f:
            lines = f.readlines()
        for line in lines:
            if "session_id" in line:
                session_id = line.split()[1]
            if "executor_url" in line:
                executor_url = line.split()[1]
        logging.info("Trying to resume an existing browser session from fetched credentials")
        driver = launchChrome(remote=True, session_id=session_id, executor_url=executor_url)
        logging.info(driver.current_url)
    except:
        logging.info("Didn't work, opening a new browser window and getting new credentials")
        driver = get_new_credentials()

    return (driver)


# Read messages
def read_msgs(data):

    logging.info("Let's find the 'Group' on the web page")
    time.sleep(1)
    try:
        elem = driver.find_element_by_xpath('//span[contains(@title, "{}")]'.format(args.group))
        elem.click()
    except:
        logging.info("Cannot find the Group. Try again")
        return -1

    logging.info("Read messages from the 'group'")
    time.sleep(1)

    elems = driver.find_elements_by_class_name("Tkt2p")
    for elem in elems:
        msg = elem.find_element_by_class_name("_3zb-j")
        tim = elem.find_element_by_class_name("_2f-RV")
        # Only append message if identifier found in the msg, discard otherwise
        if args.identifier in msg.text:
            logging.info("Identifier found. Adding entry to DataFrame")
            data.loc[len(data)] = [pd.to_datetime(tim.text), msg.text, False]
            # Drop duplicates from the DataFrame
            data = data.drop_duplicates(subset=["time", "message"])

    return data


# Get auto generated context message from AI model
def get_reply_msg(text):
    raw_msg = reply(text)


# Reply to a message
def reply_msg(text):

    # Calling function to get auto generated message from the AI model
#    msg = get_reply_msg(text)

    time.sleep(2)
    logging.info("Selecting the input box")
    inp_xpath = '//div[@class="_2S1VP copyable-text selectable-text"][@contenteditable="true"][@data-tab="1"]'

    # Go forward only if input box is found on the web page. Else return False
    try:
        input_box = driver.find_element_by_xpath(inp_xpath)
    except:
        logging.info("Unable to find the input box the target group")
        return False
    time.sleep(2)
    logging.info("Sending message: {}".format(text))

    # Return True if the message is sent to the group. Else return False
    try:
        input_box.send_keys(text + Keys.ENTER)
        time.sleep(2)
        return True
    except:
        logging.info("Unable to send message to the target group")
        return False


if __name__ == "__main__":

    # Get Chrome browser driver, either existing or a new one
    driver = get_driver()
    # Only get "https://web.whatsapp.com" if it's not already set in the existing browser
    if driver.current_url != args.url:
        logging.info("Current URL not 'target', calling 'target' URL")
        driver.get(args.url)
        input("Scan QR Code, and then hit Carriage Return >>")
        print("Logged In")

'''
    # Create a dummy pandas DataFrame to hold messages
    data = pd.DataFrame(columns=["time", "message", "isreplied"])

    # Create an infinite loop periodically check web page for new messages
    while (True):
        # Read messages and fill the messages in the pandas DataFrame
        data = read_msgs(data)

        # Go over the contents of the DataFrame and reply to messages which haven't already been replied
        for i, msg in enumerate(data["message"]):
            if not data["isreplied"][i]:
                logging.info("Message: {} is not yet replied".format(msg))
                isreplied = reply_msg(msg)
                data["isreplied"][i] = isreplied
                if not isreplied:
                    logging.info("Something wrong with the reply_msg() function. Exiting..")
                    break
        time.sleep(args.periodicity)
'''