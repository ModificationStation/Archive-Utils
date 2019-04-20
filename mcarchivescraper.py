import os
import requests
import bs4
import io
import urllib3

def match_class(target):
    def do_match(tag):
        classes = tag.get('class', [])
        return all(c in classes for c in target)
    return do_match

site = "https://mcarchive.net"
mods = []
parentDir = "./mcarchivescraper_data"

try:
    os.mkdir(parentDir)
except:
    pass

os.chdir(parentDir)
first = True

with requests.get(site + "/mods") as response:
    siteData = response.text

    siteDict = bs4.BeautifulSoup(siteData, "html.parser")

    for mod in siteDict.findAll(match_class(["block"])):
        if first:
            first = False
        else:
            mod = mod.find("a").get("href")
            mods.append(mod)

downloaded = 0

for mod in mods:
    with requests.get(site + mod) as response:
        page = bs4.BeautifulSoup(response.text, "html.parser")
        print("Parsing " + site + mod)
        for link in page.findAll(match_class(["btn"])):
            if link.contents[0].strip() == "IPFS Download":
                try:
                    name = os.path.basename(link.get("href"))
                    if os.path.exists(name):
                        print("\"" + name + "\" exists. Skipping.")
                    else:
                        print("Trying to download \"" + name + "\"")
                        with requests.get(link.get("href"), stream=True, timeout=20) as response:
                            with io.open(name, 'wb') as fd:
                                oldDone = 0
                                for chunk in response.iter_content(chunk_size=4096):
                                    fd.write(chunk)
                    downloaded += 1
                except Exception as e:
                    print(e)
                    try:
                        os.unlink(name)
                    except:
                        pass

print("Downloaded " + str(downloaded) + (" mod." if downloaded == 1 else "mods."))