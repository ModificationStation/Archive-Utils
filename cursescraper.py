"""
Exit codes:
-1: User termination.
0: Normal exit.
1: Generic exception.
2: Invalid arguments.
3: Missing write access.
"""

utilversion = "v0.3"
print("Cursescraper " + utilversion + " starting...")

import sys
import os
import requests
import getopt
import traceback
import bs4
import io
import shutil
import time
import contextlib
import json

helpText = """Usage: cursescraper (params)

Accepted params:
    -h: Shows this.
    -p, --parentdir <path>: Use the directory specified."""

parentDir = "cursescraper_data"

keepcharacters = (" ", ".", "_", "(", ")", "[", "]", "{", "}", "-")


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


def download(url, name, newDir=None):
    if not os.path.exists(newDir + "/" + name):
        try:
            with requests.get(url, stream=True) as response:
                total_length = int(response.headers.get("content-length"))
                dl = 0
                if response.content is None:
                    raise ConnectionError
                try:
                    os.mkdir("tmp")
                except:
                    pass

                with io.open("tmp/" + name, 'wb') as fd:
                    oldDone = 0
                    for chunk in response.iter_content(chunk_size=4096):
                        dl += len(chunk)
                        fd.write(chunk)
                        done = int(50 * dl / total_length)
                        if done != oldDone:
                            print("\r[%s%s]" % ("=" * done, " " * (50 - done)), end="")
                            oldDone = done

                print("")

            if newDir:
                shutil.move("tmp/" + name, newDir)
        except Exception as e:
            print("An exception ocurred:")
            traceback.print_exc()

    else:
        print("File \"" + newDir + "/" + name + "\" already exists! Skipping.")


def start():
    # Insert startup thingy here.
    print("Cursescraper " + utilversion + " started!\n\n")

    print("What minecraft curse site do you want to scrape?\n1: Bukkit\n2: Mods\n3: Modpacks\n4: Custom URL\n5: Exit\n\nFormat: <option>:<version> e.g. 1:CB 1060")
    selection = " "

    while not any(selection.split(":")[0] in s for s in ["1", "2", "3", "4", "5"]):
        selection = str(input("> ")).strip()
        #print("> 1:CB 1060")
        #selection = "1:CB 1060"

    site = None
    siteSub = None
    cfSite = None
    mcVersion = None

    if selection.split(":")[0] == "1":
        site = "https://dev.bukkit.org/"
        siteSub = "projects"
        siteRepo = "bukkit-plugins"
        cfSite = "https://api.cfwidget.com/minecraft/bukkit-plugins/"

    try:
        mcVersion = selection.split(":")[1]
        siteName = site.split("/")[2]
    except:
        print("Version not given. Exiting...")
        sys.exit(2)

    if not site or not cfSite or not mcVersion or not siteSub:
        print("Invalid arguments. Exiting...")
        sys.exit(2)

    print("Getting versions")
    with requests.get(site + siteRepo) as response:
        versionElements = bs4.BeautifulSoup(response.text, "html.parser").find(id="filter-game-version").find_all("option")[1:]
        versions = {}
        for element in versionElements:
            versionID = element.get("value")
            element = str(element)
            versions[element.split("\xa0\xa0")[1].split("<")[0].strip()] = versionID


    with requests.get(site + siteRepo + "?filter-game-version=" + versions[mcVersion]) as response:
        try:
            pages = bs4.BeautifulSoup(response.text, "html.parser").find_all(match_class(["b-pagination-list", "paging-list", "j-tablesorter-pager", "j-listing-pagination"]))[0]
            pages = bs4.BeautifulSoup(str(pages), "html.parser").find_all(match_class(["b-pagination-item"]))[-1]
            pages = int(str(pages).split("page=")[1].split("\"")[0])
        except IndexError:
            pages = 1

    if pages == 1:
        pagesOrPage = "page"
    else:
        pagesOrPage = "pages"
    print(str(pages) + " {0} found.".format(pagesOrPage))
    projects = {}

    for index in range(pages):
        print("Getting page " + str(index+1) + "'s info.")
        with requests.get(site + siteRepo + "?filter-game-version=" + versions[mcVersion] + "&page=" + str(index+1)) as response:  # Add +1 cause page 0 is same as page 1.
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

    try:
        os.mkdir(siteName)
    except:
        pass
    try:
        os.mkdir(siteName + "/" + mcVersion)
    except:
        pass

    for project in projects:
        project = projects[project]
        print("Downloading all versions for " + project["url"] + " on version " + mcVersion)
        with requests.get(cfSite + project["url"]) as response:
            if response.status_code == 202:
                print("API retrieving info. Waiting 5 seconds.")
                time.sleep(5)
                response = requests.get(cfSite + project["url"])

            if response.status_code != 200:
                print("Error " + str(response.status_code) + " occurred. Skipping file.")
            else:
                for file in json.loads(response.content)["files"]:
                    if mcVersion in [p.strip() for p in file["versions"]]:
                        print(site + siteSub + "/" + project["url"] + "/files/" + str(file["id"]))
                        with contextlib.closing(requests.get(site + siteSub + "/" + project["url"] + "/files/" + str(file["id"]), stream=True)) as res:
                            fileName = None
                            buffer = ""
                            for chunk in res.iter_content(chunk_size=1024, decode_unicode=True):
                                buffer = "".join([buffer, chunk])
                                siteHeader = bs4.BeautifulSoup(buffer, "html.parser")
                                try:
                                    match = siteHeader.find("title")
                                except:
                                    match = None

                                if match:
                                    match = str(match)
                                    fileName = match.split(" - ")
                                    if fileName[0].lower().strip("<title>") == "archive":
                                        fileName = fileName[3] + "-" + fileName[1].lower().strip("<title>").strip(fileName[3].lower()).strip() + ".jar"
                                    else:
                                        fileName = fileName[2] + "-" + fileName[0].lower().strip("<title>").strip(fileName[2].lower()).strip() + ".jar"
                                    fileName = "".join(c for c in fileName if c.isalnum() or c in keepcharacters).rstrip()
                                    break

                        try:
                            os.mkdir(siteName + "/" + mcVersion + "/" + project["url"])
                        except:
                            pass
                        print("Downloading " + fileName)
                        download(site + siteSub + "/" + project["url"] + "/files/" + str(file["id"]) + "/download", fileName, siteName + "/" + mcVersion + "/" + project["url"])


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

    try:
        shutil.rmtree("tmp")
    except:
        pass

    os.chdir(parentDir)

    start()
