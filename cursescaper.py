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

utilversion = "v0.2"

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
    cfSite = None

    if selection == "1":
        site = "https://dev.bukkit.org/bukkit-plugins"
        cfSite = "https://api.cfwidget.com/minecraft/bukkit-plugins/"

    if not site or not cfSite:
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

    print(str(pages) + " pages found.")
    projects = {}

    for index in range(pages):
        print("Getting page " + str(index+1) + "'s info.")
        with requests.get(site + "?filter-game-version=" + versions["CB 1060"] + "&page=" + str(index+1)) as response:  # Add +1 cause page 0 is same as page 1.
            if response.status_code != 200:
                break
            else:
                page = bs4.BeautifulSoup(response.text, "html.parser")
                page = page.findAll(match_class(["project-list-item"]))
                count = 0
                for project in page:
                    count += 1
                    projectInfo = project.find(match_class(["name-wrapper", "overflow-tip"]))
                    projects[projectInfo.find("a").get_text().strip()] = {}
                    projects[projectInfo.find("a").get_text().strip()]["url"] = projectInfo.find("a").get("href").split("/")[2]
                print("Parsed " + str(count) + " projects.\n")

    for name in projects:
        info = projects[name]
        print("Downloading information for " + name)
        url = cfSite + info["url"]
        print(url)





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