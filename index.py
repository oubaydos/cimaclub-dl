import enum
import re

from logger import logging
from bs4 import BeautifulSoup
import requests

port = "2096"
cimaclub = f"https://www.cima-club.cc:{port}/"


def get_multiple_download_links(url_list: list):
    L = []
    for i in url_list:
        print("calling get_download_links for ",url_list.index(i)," ",type(i))
        try:
            L.append(get_download_links(i))
        except RuntimeError:
            L.append(None)
    return L


def get_download_links(url: str):
    """
    :param url: the download link - should be in the form : https://www.cima-club.cc:..../watch/....
    :return: a list of the download links --> watch out, there will be other links in there
    """
    response = requests.get(url)
    content = BeautifulSoup(response.text, "html.parser")
    downloads_links = content.select_one('div[class*="downloads"]')
    if downloads_links is None:
        raise RuntimeError("downloads section not found")
    download_link = ""
    # print(downloads_links.findChildren("a")[0]["href"])
    for i in downloads_links.findChildren("a"):
        if "gvid" in i["href"] or "govid" in i["href"]:
            download_link = i["href"]
            break
    if download_link == "":
        raise RuntimeError("download link not found")  # gvid links not found
    req = requests.get(download_link)
    if not str(req.status_code).startswith("2"):
        logging.error("govid server is unreachable")
        return []
    download_page = BeautifulSoup(req.text, 'html.parser')

    L = []
    for i in download_page.find_all("a"):
        L.append(i["href"])
    return L


class Type(enum.Enum):
    movie = 1
    series = 2


# add a regex validation for season_link
def get_episodes_links(season_link: str):
    if season_link.endswith("/"):
        season_link = season_link[:-1]
    response = requests.get(season_link + "/episodes")
    content = BeautifulSoup(response.text, "html.parser")
    episodes_div = content.select('div[class*="media-block"] > div[class="content-box"]')
    if len(episodes_div) == 0:
        logging.error("could not extract episode links from found season link")
        return []
    episodes_links = [None] * len(episodes_div)
    for i in episodes_div:
        if i.span.em is not None and i.a["href"] is not None:
            episodes_links[int(i.span.em.text) - 1] = i.a["href"]
    while episodes_links[-1] is None:
        episodes_links.pop()
    return episodes_links


def search(title: str, movie_or_series: Type):
    search_result = BeautifulSoup(requests.get(cimaclub + "search", params={"s": title}).text, 'html.parser')
    links = []
    titles = []
    # we will now handle only movies :
    for i in search_result.select('div[class*="media-block"] > div'):
        a = i.find_all('a')[-1]
        if movie_or_series == Type.movie and "series" not in a["href"] and 'season' not in a["href"]:
            links.append(a["href"])
            titles.append(a.text)
        elif movie_or_series == Type.series and ("series" in a["href"] or 'season' in a["href"]):
            links.append(a["href"])
            titles.append(a.text)
    # print(links,titles,sep='\n')
    assert len(links) == len(titles)
    for i in range(len(titles)):
        print(f"({titles[i]} : ({i + 1})")
    chosen = int(input("please choose a title : ")) - 1
    assert 0 <= chosen < len(titles)
    a = links[chosen]
    if movie_or_series == Type.movie:
        a = a.replace("film", "watch")
        print(a)
        return [a]
    elif 'season' in a:
        episodes = get_episodes_links(a)
        for i in episodes:
            if i is not None:
                print(i)
        # add the option to get the whole season
        chosen_episode = input(
            f"please choose the episodes to download (firstEpisode-lastEpisode): (1-{len(episodes)}) : ")
        if chosen_episode.isnumeric():
            assert 0 < int(chosen_episode) <= len(episodes)
            a = episodes[int(chosen_episode) - 1]
            if a is not None:
                a = a.replace("episode", "watch")

        else:
            assert "-" in chosen_episode and len(chosen_episode.split("-")) == 2
            episode1 = chosen_episode.split("-")[0]
            episode2 = chosen_episode.split("-")[1]
            assert episode1.isnumeric() and episode2.isnumeric() and 0 < int(episode1) <= len(episodes) and 0 < int(
                episode2) <= len(episodes) and int(episode1) <= int(episode2)
            a = episodes[int(episode1) - 1:int(episode2)]
        print(a)
        return a

def beautify_multiple_download_links(links:list):
    L = []
    for i in links:
        if i is not None:
            L.append(beautify_download_links(i))
    return L
def beautify_download_links(links: list):
    quality_link = {}
    counter = 1
    for i in links:
        if "aac-480" in i:
            quality_link["480"] = i
        elif "aac-720" in i:
            quality_link["720"] = i
        elif "aac-1080" in i:
            quality_link["1080"] = i
        # elif any(char.isdigit() for char in i) or "cimaclub" in i.lower():
        #     quality_link["other quality " + str(counter)] = i
        #     counter += 1
    return quality_link

def choose_quality_for_multiple_download(links:list):
    for i in links:
        choose_quality(i)
def choose_quality(links: dict):
    print("available qualities : ", end="")
    for i in links.keys():
        print(i, end=", ")
    print()
    quality = str(input("please choose a quality : "))
    if quality in links.keys():
        print(links[quality])
    else:
        print("quality not found!!")
        choose_quality(links)


def main():
    # now you need to add a beautify_multiple_download_links and handle errors
    title = input("please enter the title you are looking for : ")
    print("(1) movie\n(2) series")
    choice = int(input("enter the type : "))
    assert choice == 1 or choice == 2
    type = Type.movie if choice == 1 else Type.series
    link = search(title, type)
    download_links = get_multiple_download_links(link)
    print(download_links)
    links_dict = beautify_multiple_download_links(download_links)
    choose_quality_for_multiple_download(links_dict)
    ##there is a pb with movies; i looked for young with type 1 and returned series 


if __name__ == "__main__":
    main()
