import json
from bs4 import BeautifulSoup
import requests
import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector

CHART_DICT = {
    'title': "",
    'type': "",
    'url': "",
    'image_path': "",
    'source': "",
    'description': "",
    'wikipedia_pages': []
}


def get_lang_detector(nlp, name):
    return LanguageDetector(seed=42)  # We use the seed 42

COMMONS_CHART_URL = "https://commons.wikimedia.org/{}"
NLP_MODEL = spacy.load("en_core_web_sm")
Language.factory("language_detector", func=get_lang_detector)
NLP_MODEL.add_pipe('language_detector', last=True)


def get_english_description(chart_page):
    for td_item in chart_page.find_all("td", {"class": "description"}):
        item = td_item
        if td_item.find_all("div"):
            item = td_item.find_all("div")[0]

        doc = NLP_MODEL(item.text)
        for i, sent in enumerate(doc.sents):
            # if language not english and probability > 0.5 stop
            if sent._.language["language"] != "en" and sent._.language["score"] > 0.5:
                return None
            else:
                description = item.text
                if "English: " in description:
                    description = description.split("English: ")[1:][0].strip()
                return description


def get_wiki_links(chart_page):
    wiki_links = []
    page_items = chart_page.find_all("div", {"id": "mw-imagepage-section-globalusage"})

    if page_items and len(page_items) > 0:
        for wiki_link_item in page_items[0].find_all("a"):
            wiki_links.append(wiki_link_item["href"])

    return wiki_links


def extract_chart(chart_link, chart_type):
    # access single chart image page, e.g. "https://commons.wikimedia.org/wiki/File:1_guadeloupe_pesticides.jpg"
    chart_response = requests.get(chart_link)
    chart_page = BeautifulSoup(chart_response.content, "html.parser")

    # check if English chart, extract description
    description = get_english_description(chart_page)
    if not description or description is None:
        print(f"{chart_link} non-english chart!")
        return None

    # extract Wikipedia pages using this chart
    wiki_links = get_wiki_links(chart_page)

    # extract source
    source_link = chart_page.find_all("a", {"class": "external free"})
    source = ""
    if source_link:
        source = source_link[0]["href"]

    # save chart image locally
    image_filename = ""
    for img_item in chart_page.find_all("img"):
        if "File:" in img_item["alt"]: # select chart image
            img_response = requests.get(img_item["src"])
            image_filename = "".join(chart_link.split("File:")[1:])
            with open("../data/images/{}".format(image_filename), 'wb') as f:
                f.write(img_response.content)

    # save chart dict
    chart_dict_copy = CHART_DICT.copy()
    chart_dict_copy["title"] = chart_page.title.text
    chart_dict_copy["type"] = chart_type
    chart_dict_copy["url"] = chart_link
    chart_dict_copy["image_path"] = image_filename
    chart_dict_copy["source"] = source
    chart_dict_copy["description"] = description
    chart_dict_copy["wikipedia_pages"] = wiki_links

    return chart_dict_copy


def create_chart_dataset(page, chart_type):
    # load website
    response = requests.get(page)
    page_content = BeautifulSoup(response.content, "html.parser")
    chart_image_list = []

    # if next page and go to next page first
    for link in page_content.find_all("a"):
        if link.text.strip() == "next page":
            next_page_link = COMMONS_CHART_URL.format(link["href"])
            chart_image_list = create_chart_dataset(next_page_link, chart_type)

    # iterate over images on overview page
    for item in page_content.find_all('li', {"class": "gallerybox"})[:10]:
        # for each image retrieve link to its page
        chart_link = COMMONS_CHART_URL.format(item.find_all('a')[1]["href"])

        # extract and save chart (content)
        chart_dict_copy = extract_chart(chart_link, chart_type)

        if chart_dict_copy:
            chart_image_list.append(chart_dict_copy)

    return chart_image_list


def main():
    page = "https://commons.wikimedia.org/wiki/Category:Horizontal_bar_charts"
    chart_type = "barchart_horizontal"

    chart_image_list = create_chart_dataset(page, chart_type)

    # save chart_image_list
    with open(r"../data/horizontal_bar_charts.json", "w", encoding="utf-8") as file:
        json.dump(chart_image_list, file, indent=4)


if __name__ == '__main__':
    main()
