import json
import time

import requests
import spacy
from bs4 import BeautifulSoup
from spacy.language import Language
from spacy_language_detection import LanguageDetector

CHART_DICT = {
    'file_name': "",
    'type': "",
    'url': "",
    'source': "",
    'description': "",
    'wikipedia_pages': []
}
HEADERS = {
  'User-Agent': 'mubashara.akhtar@kcl.ac.uk'
}
CATEGORY_URL = "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:{}&cmlimit=500&cmtype=file&format=json"
COMMONS_FILE_URL = "https://api.wikimedia.org/core/v1/commons/file/"
COMMONS_CHART_URL = "https://commons.wikimedia.org/{}"


def get_lang_detector(nlp, name):
    return LanguageDetector(seed=42)  # We use the seed 42

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


def extract_chart(chart_page_url, chart_image_url, chart_type, image_filename=""):
    # access single chart image page, e.g. "https://commons.wikimedia.org/wiki/File:1_guadeloupe_pesticides.jpg"
    chart_response = requests.get("https:"+chart_page_url, HEADERS, stream=True)
    chart_page = BeautifulSoup(chart_response.content, "html.parser")

    # check if English chart, extract description
    description = get_english_description(chart_page)
    if not description or description is None:
        print(f"{chart_page_url} non-english chart!")
        return None

    # extract Wikipedia pages using this chart
    wiki_links = get_wiki_links(chart_page)

    # extract source
    source_link = chart_page.find_all("a", {"class": "external free"})
    source = ""
    if source_link:
        source = source_link[0]["href"]

    # save chart image locally
    if "http" not in chart_image_url:
        chart_image_url = "https:" + chart_image_url
    img_response = requests.get(chart_image_url, headers=HEADERS, stream=True)
    try:
        with open(r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\images\{}".format(image_filename),
                  'wb') as f:
            f.write(img_response.content)
    except FileNotFoundError:
        # shorten file name to overcome error of too long file names specific to Python/Windows setting
        image_filename_parts = image_filename.split(".")
        image_filename = image_filename_parts[0][:100] + "." + image_filename_parts[1]
        with open(r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\images\{}".format(image_filename),
                  'wb') as f:
            f.write(img_response.content)

    # save chart dict
    chart_dict_copy = CHART_DICT.copy()
    chart_dict_copy["file_name"] = image_filename
    chart_dict_copy["type"] = chart_type
    chart_dict_copy["url"] = chart_page_url
    chart_dict_copy["source"] = source
    chart_dict_copy["description"] = description
    chart_dict_copy["wikipedia_pages"] = wiki_links

    return chart_dict_copy


def create_chart_dataset(page, chart_type):
    chart_image_list = []
    has_more_items = False

    # retrieve all images of the given category "page"
    category_url = CATEGORY_URL.format(page)
    response = requests.get(category_url, headers=HEADERS, stream=True)
    time.sleep(10)
    response_json = response.json()
    chart_pages_list = response_json["query"]["categorymembers"]
    if "continue" in response_json.keys():
        # category has multiple pages of items
        has_more_items = True

    while has_more_items:
        # iterate until the category has a followup page
        category_url_continue = category_url + "&cmcontinue=" + response_json["continue"]["cmcontinue"] + "&continue=" + response_json["continue"]["continue"]
        response = requests.get(category_url_continue, headers=HEADERS, stream=True)
        time.sleep(10)
        response_json = response.json()
        chart_pages_list.extend(response_json["query"]["categorymembers"])
        if "continue" not in response_json.keys():
            has_more_items = False

    # iterate over retrieved image entries
    for image_entry in chart_pages_list:
        # get url for page showing image and details
        url = COMMONS_FILE_URL + image_entry["title"]
        try:
            response = requests.get(url, headers=HEADERS, stream=True)
        except Exception as e:
            print(f"The following error occurred for entry {image_entry}: {e}.")

        image_content = response.json()
        if "file_description_url" in image_content.keys():
            image_url = image_content["file_description_url"]
            image_filename = "".join(image_content["file_description_url"].split("File:")[1:])
        elif "title" in image_content.keys():
            image_url = url
            image_filename = "".join(image_content["title"].split("File:")[1:])
        else:
            # image was not retrieved correctly
            print(f"Skipping entry {image_entry}. Doing a timeout. ")
            time.sleep(2400)
            continue

        # extract image file and relevant data
        chart_dict_copy = extract_chart(chart_page_url=image_url, chart_image_url=image_content["preferred"]["url"],
                                        chart_type=chart_type, image_filename=image_filename)
        if chart_dict_copy:
            # information retrieval successful, add entry to dataset list
            chart_image_list.append(chart_dict_copy)

    return chart_image_list


def main():
    # wikimedia categories to extract data from
    chart_categories_dict = {
        # "barchart_horizontal": "Horizontal_bar_charts",
        # "barchart_vertical": "Vertical_bar_charts",
        # "line_chart": "Line_charts",
        "pie_chart": "Pie_charts_in_English",
        # "scatter_plot": "Scatterplots",

    }
    chart_image_list = []
    for chart_type, page in chart_categories_dict.items():
        chart_image_list.append(create_chart_dataset(page, chart_type))

    # save chart_image_list @todo adjust file name
    with open(r"../data/dataset/pie_chart.json", "w", encoding="utf-8") as file:
        json.dump(chart_image_list, file, indent=4)


if __name__ == '__main__':
    main()
