import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import argparse
import json
import os
import re
import time
from random import randint


parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("r"), help="text file with list of domains.")
parser.add_argument("-t", "--timing", help="shows timing of each operation.", action="store_true")
args = parser.parse_args()


def get_whois(url):
    """
    Returns html whois page from who.is.

    :param url: domain
    :return: html page
    """
    print("Getting data for %s. " % url, sep="", end="", flush=True)
    ua = UserAgent()
    headers = {
        "Referer": "https://who.is/",
        "User-Agent": ua.firefox}
    time_sleep = randint(250, 2000) / 1000
    time.sleep(time_sleep)
    time_access1 = time.time()
    whois = requests.get("https://who.is/whois/" + url, headers=headers)
    time_access = (time.time() - time_access1)
    if args.timing:
        print("Got. Access time %.3fs (delay %.3fs)" % (time_access, time_sleep), sep="", flush=True)
    else:
        print("Got.", sep="", flush=True)

    return whois.text


def rawwhois_parse(rawwhoises):
    """
    Returns dict of parsed text (structured) from Registrar Data block.

    :param rawwhoises: bs4.element.Tag
    :return: dict
    """
    result = {}
    for rawwhois in rawwhoises:
        head = rawwhois.find("div")
        strns = rawwhois.find_all("div", {"class": "row"})
        part = {}
        for strn in strns:
            key_str = strn.find("div", {"class": "col-md-4"})
            value_str = strn.find("div", {"class": "col-md-7"})
            part[key_str.get_text()] = value_str.get_text()
            result[head.get_text()] = part

    return result


def plain_text_parse(text):
    """
    Returns dict of parsed text (plain) from Registrar Data block or list if text is Similar Domains row

    :param text: str
    :return: dict
    """
    if re.findall("\s\|\s", text):
        return re.split("\s\|\s", text.replace("\n", ""))[:-1]

    step1 = re.sub("(?m)^%.*\n?|^\n", "", text)
    step2 = re.sub("</?\w+>", "\n", step1)
    step3 = re.sub("\n+", "\n", step2)
    step4 = step3.splitlines()

    step5_list = []
    for line in step4:
        step5_list.append(re.split(":[\s\t]+", line))

    result = {}
    for item in step5_list:
        if len(item) > 1:
            result[item[0]] = item[1]
        else:
            result[item[0]] = ""

    return result


def value_parse(lists):
    """
    Returns list of multiple values of string value

    :param lists: list
    :return: list or str
    """
    step3 = []
    if len(lists) > 1:
        for item in lists:
            step1 = re.split("</?.+?>", str(item))
            for i in step1:
                if re.findall("^[\s\t]+", i) or not i:
                    continue
                step3.append(re.sub("\n+", "", i))
    else:
        for item in lists:
            step1 = re.split("</?.+?>", item)
            for i in step1:
                if re.findall("^[\s\t]+", i) or not i:
                    continue
                step3.append(re.sub("\n+", "", i))
    if len(step3) == 1:

        return "".join(step3)
    else:
        return step3


def do_parse(html):
    """
    Returns dict of parsed https://who.is/whois/* page

    :param html: html page
    :return: dict
    """
    whois_text = html
    soup = BeautifulSoup(whois_text, "html.parser")
    rows = soup.find("div", {"class": "queryResponseContainer"}).find_all("div", {"class": "row"}, recursive=False)
    data = {}
    for i in range(1, 10, 2):  # by structure in odd rows are heads and in even rows are tables
        lines = rows[i+1].find_all("div", {"class": "queryResponseBodyRow"})  # heads
        part1 = {}
        part2 = {}
        for line in lines:  # tables from keys (optional) and values (must)
            keys = line.find_all("div", {"class": "queryResponseBodyKey"})
            if keys:
                values = line.find_all("div", {"class": "queryResponseBodyValue"})
                for key, value in zip(keys, values):
                    part1[key.get_text()] = value_parse(value.contents)
            else:  # rows without key are Similar Domains with string with a specific separator and
                # Registrar Data with plain text with self structure
                values = line.find_all("div", {"class": "queryResponseBodyValue"})
                for value in values:
                    rawwhoises = value.find("div", {"class": "rawWhois"})
                    if rawwhoises:  # structured text in Registrar Data
                        part2 = rawwhois_parse(rawwhoises)
                    else:
                        part2 = plain_text_parse(value.get_text())
        if part2:
            data[rows[i].find("span", {"class": "lead"}).get_text()] = part2
        else:
            data[rows[i].find("span", {"class": "lead"}).get_text()] = part1

    return data


def save_dump():
    """
    Saves scrapped data to the json file

    :return: .json file
    """
    print("\nSaving data... ", sep="", end="", flush=True)
    with open("dump.json", "w") as json_file:
        json.dump(all_data, json_file)
    time_elapsed = time.time() - time_start
    print("Done.\nOutput json file placed to {}/dump.json\nElapsed time: {:.0f}m {:.0f}s".format(os.getcwd(),
                                                                                                 time_elapsed / 60,
                                                                                                 time_elapsed % 60))


def work():
    """
    Creates json file with all scrapped pages

    :return: dump.json
    """
    global time_start, all_data
    time_start = time.time()
    all_data = {}
    check_list = args.file.readlines()
    for i, line in enumerate(check_list, 1):
        url = line[:-1]
        print("%d/%d " % (i, len(check_list)), sep="", end="", flush=True)
        data = do_parse(get_whois(url))
        all_data[url] = data
    save_dump()


if __name__ == '__main__':
    try:
        work()
    except KeyboardInterrupt:
        save_dump()
