import bs4
import json
import simplejson

file = open("page.html", "r")

page = bs4.BeautifulSoup(file.read(), "html.parser")

lis = []
files = {}

for li in page.find_all("li"):

    links = li.find_all("a")

    for link in links:
        url = link.get("href")

        if url.__contains__("launcher.mojang.com") and url.__contains__("client.jar"):
            files[li.get("id")] = url.split("objects/")[1].split("/client.jar")[0]

file.close()
file = open("out.json", "w")

file.write(simplejson.dumps(files, indent=4))
