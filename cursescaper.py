"""
Exit codes:
-1: User termination.
0: Normal exit.
1: Generic exception.
2: Invalid arguments.
3: Missing write access.
"""

import sys
import os
import requests
import getopt
import traceback
import bs4
import pprint

utilversion = "v0.1"

helpText = """Usage: cursescraper (params)

Accepted params:
    -h: Shows this.
    -p, --parentdir <path>: Use the directory specified."""

parentDir = "cursescraper_data"


def getURLAsFile(url, filepath):
    print("Getting \"" + url + "\" and storing it in \"" + filepath + "\".")
    with requests.get(url) as response:
        if response.status_code == 200:
            with open(filepath, "w") as file:
                file.write(response.content)
        else:
            print("URL responded with error code " + str(response.status_code) + " for URL \"" + url + "\".")


def match_class(target):
    def do_match(tag):
        classes = tag.get('class', [])
        return all(c in classes for c in target)
    return do_match



def start():
    print("Cursescraper " + utilversion + " starting...")
    # Insert startup thingy here.
    print("Cursescraper " + utilversion + " started!\n\n")

    print("What minecraft curse site do you want to scrape?\n1: Bukkit\n2: Mods\n3: Modpacks\n4: Custom URL\n5: Exit")
    selection = "0"

    while not any(selection in s for s in ["1", "2", "3", "4", "5"]):
        selection = str(input("> "))

    site = None

    if selection == "1":
        site = "https://dev.bukkit.org/bukkit-plugins"

    if not site:
        print("Site not declared. Exiting...")
        sys.exit(2)

    print("Getting versions")
    with requests.get(site) as response:
        versionElements = bs4.BeautifulSoup(response.text, "html.parser").find(id="filter-game-version").find_all("option")[1:]
        versions = {}
        for element in versionElements:
            versionID = element.get("value")
            element = str(element)
            versions[element.split("\xa0\xa0")[1].split("<")[0].strip()] = versionID

    with requests.get(site + "?filter-game-version=" + versions["CB 1060"]) as response:
        pages = bs4.BeautifulSoup(response.text, "html.parser").find_all(match_class(["b-pagination-list", "paging-list", "j-tablesorter-pager", "j-listing-pagination"]))[0]
        pages = bs4.BeautifulSoup(str(pages), "html.parser").find_all(match_class(["b-pagination-item"]))[-1]
        pages = int(str(pages).split("page=")[1].split("\"")[0])

    print(pages)

    for index in range(pages+1): # +1 cause it runs from 1, not 0.
        with requests.get(site + "?filter-game-version=" + versions["CB 1060"] + "&page=" + str(index)) as response:
            if response.status_code != 200:
                break
            else:
                page = bs4.BeautifulSoup(response.text, "html.parser")
                page = page.findAll(match_class(["project-list-item"]))
                for project in page:
                    print(project.find(match_class(["name-wrapper", "overflow-tip"])).get_text())







if __name__ == '__main__':
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hp:", ["parentdir="])
    except getopt.GetoptError:
        print(helpText)
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(helpText)
            sys.exit()
        elif opt in ("-p", "--parentdir"):
            parentDir = arg

    try:
        os.mkdir(parentDir)
    except Exception as e:
        if not str(e).lower().__contains__("file already exists"):
            traceback.print_exc()
            print("Could not make data folder.\nDo you have write access?")
            sys.exit(3)

    os.chdir(parentDir)

    start()