import pandas as pd
import argparse

parser = argparse.ArgumentParser(
    description="Parse your exported WhatsApp chat and set up your data-set.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--input_txt_file", type=str, default="wachat.txt", help="Name of the input txt file / exported WhatsApp group chat")
parser.add_argument("--output_pkl_file", type=str, default="wachat.pkl", help="Name of the output pkl file")


# Function takes WhatsApp chat export file (txt), parses through it
# and outputs a dataframe, save it into a pickle file and return the
# pkl file name.
def parse():

    args = parser.parse_args()

    # Open WhatsApp chat file
    f = open(args.input_txt_file, "r", encoding="utf-8")
    lines = f.readlines()

    # Merge multi-line messages into single list elements
    line = ""
    msgs = []
    for l in lines:
        if l.count("/") >= 2 & l.count(":") >= 2:
            if l.split("/")[0].isnumeric():
                if line != "":
                    msgs.append(line)
                    line = ""
        line += l

    # Dump it all into a single-column pandas DataFrame
    data = pd.DataFrame({"line": msgs})

    # Add timestamp columns
    data["datetime"] = [pd.to_datetime(str(i).split("-")[0])
                        for i in data["line"]]
    data["month"] = [i.month for i in data["datetime"]]
    data["year"] = [i.year for i in data["datetime"]]
    data["hour"] = [i.hour for i in data["datetime"]]
    data["minute"] = [i.minute for i in data["datetime"]]

    days = ["Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"]
    data["day"] = [days[i.weekday()] for i in data["datetime"]]

    # Add name, message and message length
    data["name"] = [str(i).split("- ")[1].split(":")[0]
                   for i in data["line"]]
    # drop rows where name is longer than 22 chars
    data = data[data["name"].map(len) < 22]

    data["msg"] = [str(i).split("- ")[1].split(":")[1]
                   for i in data["line"]]
    data["len"] = [len(str(i)) for i in data["msg"]]

    # Finally, delete the main column, we don't need it anymore
    del data["line"]

    # Save this pandas dataframe into the output pickle file
    data.to_pickle(args.output_pkl_file)
    return (data)

if __name__ == "__main__":
    data = parse()
