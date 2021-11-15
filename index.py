import enum
import time

from logger import logging
from bs4 import BeautifulSoup
import requests
import re
import webbrowser

port = "2096"
cimaclub = f"https://www.cima-club.cc:{port}/"


def get_download_links(url: str):
    """
    :param url: the download link - should be in the form : https://www.cima-club.cc:..../watch/....
    :return: a list of the download links --> watch out, there will be other links in there
    """
    response = requests.get(url)
    content = BeautifulSoup(response.text, "html.parser")
    downloads_links = content.select_one('div[class*="downloads"]')
    if downloads_links is None:
        logging.error("downloads section not found, please choose a different episode/movie to download")
        logging.error("to exit please click ctrl+c")
        raise RuntimeError()
    download_link = ""
    for i in downloads_links.findChildren("a"):
        if "gvid" in i["href"] or "govid" in i["href"]:
            download_link = i["href"]
            break
    if download_link == "":
        logging.error("download link not found, please choose a different episode/movie to download")
        logging.error("to exit please click ctrl+c")
        raise RuntimeError()  # gvid links not found
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


def extract_season_number(season_title: str):
    match = re.search(r"موسم [0-9]+", season_title)
    if not bool(match):
        return season_title
        ## i didnt want to return None
    if match.group().split()[1].isdigit():
        return match.group().split()[1]
    return match.group()


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
        elif movie_or_series == Type.series and 'season' in a["href"]:
            # changed and ("series" in a["href"] or 'season' in a["href"]) to that
            links.append(a["href"])
            titles.append(a.text)
            # logging.debug(extract_season_number(a.text))
            # now sort the links
    assert len(links) == len(titles)

    #####
    links_dict = dict()
    for i in range(len(titles)):
        links_dict[titles[i]] = links[i]
    sort_links = dict(sorted(links_dict.items(), key=lambda x: extract_season_number(x[0]), reverse=False))
    links = list(sort_links.values())
    titles = list(sort_links.keys())
    # print("hello world")
    # print(sort_links)
    #####
    for i in range(len(titles)):
        logging.info(f"{titles[i]} : ({i + 1})")
    chosen = int(input("please choose a title : ")) - 1
    while not (0 <= chosen < len(titles)):
        logging.error(f"the episode number must be between 1 and {len(titles)}")
        chosen = int(input("please choose a title : ")) - 1
    a = links[chosen]
    if movie_or_series == Type.movie:
        a = a.replace("film", "watch")
    elif 'season' in a:
        episodes = get_episodes_links(a)
        for i in episodes:
            if i is not None:
                logging.info(i)
        # add the option to get the whole season
        chosen_episode = input(f"please choose an episode : (1-{len(episodes)}) or 'all': ")
        if chosen_episode == "all":
            for i in range(len(episodes)):
                if episodes[i] is not None:
                    episodes[i] = episodes[i].replace("episode", "watch")
            return episodes
        chosen_episode = int(chosen_episode)
        while not (0 < chosen_episode <= len(episodes)):
            logging.error(f"the chosen must be between 1 and {len(episodes)}")
            chosen_episode = int(input(f"please choose an episode : (1-{len(episodes)}) : "))
        a = episodes[chosen_episode - 1]
        if a is not None:
            a = a.replace("episode", "watch")
    logging.debug(a)
    return a


def beautify_download_links(links: list):
    logging.debug("hekeeeeeeeeelo" + ''.join(str(e) for e in links))
    quality_link = {}
    for i in links:
        if "-240" in i:
            quality_link["240"] = i
        elif "-360" in i:
            quality_link["360"] = i
        elif "-480" in i:
            quality_link["480"] = i
        elif "-720" in i:
            quality_link["720"] = i
        elif "-1080" in i:  # aac-1080
            quality_link["1080"] = i
    return quality_link


def open_browser_with_link(quality: str, links: list):
    choix = input("do you wish to open these links in the default browser to start downloading ? (y)/(n)")
    if choix.lower() == "y":
        for i in links:
            webbrowser.open_new(i[quality])


def choose_quality(links: dict):
    logging.info("available qualities : " + ', '.join([str(elem) for elem in links.keys()]))
    quality = str(input("please choose a quality : "))
    if quality in links.keys():
        logging.info(links[quality])
        open_browser_with_link(quality, [links])
    else:
        logging.info("quality not found!!")
        choose_quality(links)


def save_in_txt(quality, links_list, title):
    title_with_underscore = (title.rstrip().replace(" ", "_")) + ".txt"
    file = open(title_with_underscore, "w")
    for links in links_list:
        file.write(links[quality])


def choose_multiple_quality(qualities: set, links_list: list, title: str):
    logging.info("available qualities : " + ', '.join([str(elem) for elem in qualities]))
    quality = str(input("please choose a quality : "))
    if quality in qualities:
        store_in_txt = input("do you wish links to be stored in a txt file ? (y/n) : ")
        if store_in_txt == "y":
            save_in_txt(quality, links_list, title)
        for links in links_list:
            logging.info(links[quality])
        open_browser_with_link(quality, links_list)
    else:
        logging.info("quality not found!!")
        choose_multiple_quality(qualities, links_list, title)


def main():
    title = input("please enter the title you are looking for : ")
    logging.info("(1) movie\n(2) series")
    choice = int(input("enter the type : "))
    while not (choice == 1 or choice == 2):
        logging.error(f"the choice is 1 or 2 -_-")
        choice = int(input("enter the type : "))
    type = Type.movie if choice == 1 else Type.series
    link = search(title, type)

    if isinstance(link, list):
        download_links = []
        qualities = []
        for i in range(len(link)):
            links = beautify_download_links(get_download_links(link[i]))
            download_links.append(links)
            qualities.append(list(links.keys()))
        choose_multiple_quality(set.intersection(*map(set, qualities)), download_links, title)

        return
    links_dict = beautify_download_links(get_download_links(link))
    choose_quality(links_dict)
    # there is a mix between films and movies
    # there is a pb when selecting a series and not a season
    # for now i will be hiding the option to access a series ( you will still have the access to seasons )


if __name__ == "__main__":
    main()

# add the option to download with the best quality avalaible
