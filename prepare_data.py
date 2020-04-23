import pandas as pd
import langdetect as ld

import argparse

parser = argparse.ArgumentParser(
    description="Clean your data-set, apply filters and export a txt file.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# Input and output files
parser.add_argument("--input_pkl_file", type=str, default="wachat.pkl", help="Name of the input pkl file")
parser.add_argument("--output_txt_file", type=str, default="training_data.txt", help="Name of the output text file to be used for training the model")

# Data filters
parser.add_argument("--names", type=str, default="Farhan Mirani", help="Comma separated names to be filtered in the data. Ex: >Farhan Mirani, Abdul Malik")
parser.add_argument("--minyear", type=int, default=2017, help="Starting year")
parser.add_argument("--maxyear", type=int, default=2020, help="Ending year")
parser.add_argument("--minmonth", type=int, default=1, help="Starting month")
parser.add_argument("--maxmonth", type=int, default=12, help="Ending month")
parser.add_argument("--minlen", type=int, default=20, help="Shortest length of the messages")
parser.add_argument("--maxlen", type=int, default=10000, help="Longest length of the messages")
parser.add_argument("--bad_words", type=str, default="http, https", help="Comma separated words of words to exclude. Ex: >http, https")
parser.add_argument("--onlyeng", type=bool, default=True, help="Allows to filter out non-english messages from the data-set")

# This function prepares data for the model training
def prepare():

    args = parser.parse_args()

    # Read data from pkl file
    data = pd.read_pickle(args.input_pkl_file)

    # Change this section to modify/clean your original data-set
    data = data.replace(to_replace="Imran Latif Official", value="Imran Latif")
    data = data.replace(to_replace="Usman Massy", value="Usman Bhatti")

    # Create filters to apply to the data-set
    name = [name for name in args.names.split(", ")]    # name = ["name1", "name2"]
    year = [args.minyear, args.maxyear]                 # year = [yearMin, yearMax]
    month = [args.minmonth, args.maxmonth]              # month = [monthMin, monthMax]
    len = [args.minlen, args.maxlen]                    # len = [lenMin, lenMax]
    bad_words = [word for word in args.bad_words.split(", ")] # List of No-No words

    # Create a new filtered data-set "fdata"
    fdata = data[(data["name"].isin(name)) &
                (data["year"] >= year[0]) &
                (data["year"] <= year[1]) &
                (data["month"] >= month[0]) &
                (data["month"] <= month[1]) &
                (data["len"] >= len[0]) &
                (data["len"] <= len[1])
                ]

    # Extract all the messages in the filtered data-set
    # Discard messages with No-No words
    # Only include messages which have atleast some English
    msgs = []
    for msg in fdata["msg"]:
        if not any(i in msg for i in bad_words):
            if not args.onlyeng:
                msgs.append(msg)
            else:
                try:
                    if ld.detect(msg) == "en":
                        msgs.append(msg)
                except:
                    pass

    # Add message text delimiters
    msgs = ["<|startoftext|>" + msg.strip() + "<|endoftext|>\n"
            for msg in msgs]

    # Export it all to a text file in the root folder
    with open(args.output_txt_file, "w", encoding="utf-8") as f:
      for msg in msgs:
        f.write(msg)


if __name__ == "__main__":
    prepare()