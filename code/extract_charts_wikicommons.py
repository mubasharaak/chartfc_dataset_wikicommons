import json

from bs4 import BeautifulSoup


def scrape_charts(website) -> dict:
    """
    Scrapes all English charts from the given website
    :param website:
    :return: Directory with chart images and further information, e.g. source website, caption, etc.
    """
    pass


def main():
    website = ""
    chart_dict = scrape_charts(website)

    # save
    with open("", "w", encoding="utf-8") as file:
        json.dump(chart_dict, file)


if __name__ == '__main__':
    main()
