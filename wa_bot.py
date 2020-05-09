from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pandas as pd

import os, sys
from pathlib import Path

gpt_folder_name = "gpt-2-finetuning"
gpt_path = os.path.join(Path.cwd().parent, "{}/src".format(gpt_folder_name))
sys.path.insert(1, gpt_path)
from auto_reply_msg import interact_model as reply

import logging
logging.basicConfig(format='[%(asctime)s \t%(filename)s \t %(funcName)s] -\t%(message)s', level=logging.INFO)

import time
import argparse

parser = argparse.ArgumentParser(description="Fully functional WhatsApp Web bot with AI text generation.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# Arguments
parser.add_argument("--url", type=str, default="https://web.whatsapp.com/", help="WhatsApp Web URL")
parser.add_argument("--group", type=str, default="Gappi", help="Name of the 'group' for the bot to reply")
parser.add_argument("--identifier", type=str, default="@not-mirani-bot", help="Identifier found in a message triggers a reply")
parser.add_argument("--periodicity", type=int, default=5, help="Amount of time (in secs) the program waits to go check for new messages")
parser.add_argument("--cred_file", type=str, default="cred.txt", help="Name of the file containing browser credentials")

args = parser.parse_args()


def launchChrome(remote=False,
                 executor_url=None,
                 session_id=None):
    '''
    Launch a new Chrome browser window to get driver object, then
    either switch it to existing window or return new window handle
    '''
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


def get_new_credentials():
    '''
    Get new credentials from newly opened file and write it in cred.txt
    This allows to avoid opening a WhatsApp every time in a new instance of
    if Chrome browser if a previous browser session is already open.
    '''

    driver = launchChrome()
    logging.info("New browser window opened")
    executor_url = driver.command_executor._url
    session_id = driver.session_id
    logging.info("Setting new credentials in 'cred.txt' file")
    with open(args.cred_file, "w") as f:
        f.write("session_id {}\n".format(session_id))
        f.write("executor_url {}".format(executor_url))

    return (driver)


def get_driver():
    '''
    Get driver, either from an existing Chrome window or a new one
    '''
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


def read_msgs(data):
    '''
    Go through the WhatsApp Web page in the browser,
    select the chat, read messages from the chat,
    and finally add messages to the [data] with isreplied set to "False"
    '''

    logging.info("Let's find the 'Group' on the web page")
    time.sleep(1)
    try:
        elem = driver.find_element_by_xpath(
            '//span[contains(@title, "{}")]'.format(args.group))
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
            data.loc[len(data)] = [pd.to_datetime(tim.text),
                                   msg.text.replace(args.identifier, ""), False]
            # Drop duplicates from the DataFrame
            data = data.drop_duplicates(subset=["time", "message"])

    return data


def get_reply_msg(text):
    '''
    Get auto generated context message from AI model
    '''
    logging.info("Input message: {}".format(text))
    raw_msg = reply(message=text)
    logging.info("Raw output message: {}".format(raw_msg))

    formatted_msg = "not-mirani-bot: {}".format(
        raw_msg[0].split("\n\n")[1].strip())

    logging.info("Formatted output message: {}".format(formatted_msg))

    return formatted_msg


def reply_msg(text):
    '''
    Call the AI model with the input text string [text]
    Put the [msg] in the chat input box and hit enter
    '''
    msg = get_reply_msg(text)

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
    logging.info("Sending message: {}".format(msg))

    # Return True if the message is sent to the group. Else return False
    try:
        input_box.send_keys(msg + Keys.ENTER)
        time.sleep(2)
        return True
    except:
        logging.info("Unable to send message to the target group")
        return False


if __name__ == "__main__":
    '''
    Main function to handle the program flow
    Get [driver] element to manipulate browser and call WhatsApp Web URL
    Create a new DataFrame called [data] with with three columns:
      -> time
      -> message
      -> isreplied    
    Start an infinite loop to monitor incoming messages on the chat window
    '''

    start_time = pd.datetime.now()
    # Get Chrome browser driver, either existing or a new one
    driver = get_driver()

    # Only get "https://web.whatsapp.com" if it's not already set in the existing browser
    if driver.current_url != args.url:
        logging.info("Current URL not 'target', calling 'target' URL")
        driver.get(args.url)
        input("Scan QR Code, and then hit Carriage Return >>")
        print("Logged In")

    # Creating a dummy pandas DataFrame to hold messages
    data = pd.DataFrame(columns=["time", "message", "isreplied"])

    # Create an infinite loop to check web page
    # for new messages periodically
    while (True):
        # Read messages and fill the messages in the pandas DataFrame
        data = read_msgs(data)
        # Go through the dataframe and
        ## if msg is received before start_time, don't reply
        ## if msg is already replied, don't reply
        ## if msg is received after start_time and not replied yet, reply!
        for i, msg in enumerate(data["message"]):
            logging.info("Message: '{}'".format(msg))
            if data["time"][i] < start_time:
                logging.info("Msg was received before the bot started")
                data["isreplied"][i] = True
            else:
                logging.info("Msg was received after the bot started")
                if not data["isreplied"][i]:
                    logging.info("Msg is not yet replied")
                    isreplied = reply_msg(msg)
                    data["isreplied"][i] = isreplied
                    if not isreplied:
                        logging.info("Something wrong with the reply_msg() function. Exiting..")
                        break
                else:
                    logging.info("Msg is already replied")
        time.sleep(args.periodicity)