import json
import os
from collections import Counter

# load files and create overview of statistics
dir_path = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data"
chart_list = []

for file_name in os.listdir(dir_path):
    if file_name.endswith(".json"):
        print(f"File name: {file_name}.")
        with open(os.path.join(dir_path, file_name)) as file:
            chart_list.extend(json.load(file)[0])

print(f"total entries: {len(chart_list)}")
horizontal_bar_count = 0
vertical_bar_count = 0
line_count = 0
pie_count = 0
scatter_count = 0
no_description_count = 0
description_len_list = []
image_file_type = []
source_count = 0
wikipages_list_len = []

for entry in chart_list:
    # statistics for type
    if entry["type"] == "barchart_horizontal":
        horizontal_bar_count += 1
    elif entry["type"] == "barchart_vertical":
        vertical_bar_count += 1
    elif entry["type"] == "line_chart":
        line_count += 1
    elif entry["type"] == "pie_chart":
        pie_count += 1
    elif entry["type"] == "scatter_plot":
        scatter_count += 1
    else:
        print(f"Wrong or missing type for entry {entry}.")

    # statistics for description
    if entry["description"] and entry["description"] != "":
        description_len_list.append(len(entry["description"]))
    else:
        no_description_count += 1

    # statistics image file type
    if entry["file_name"]:
        image_file_type.append(entry["file_name"].split(".")[-1])

    # stats source
    if entry["source"] and "/wiki/user:" not in entry["source"]:
        source_count += 1

    # stats wiki pages
    wikipages_list_len.append(len(entry["wikipedia_pages"]))

# print and save statistics
print("----------------------------- CHART DATASET STATISTICS -----------------------------")
print("------------------------------------------------------------------------------------")
print("Chart types: ")
print(f"horizontal_bar_count: {horizontal_bar_count}")
print(f"vertical_bar_count: {vertical_bar_count}")
print(f"line_count: {line_count}")
print(f"pie_count: {pie_count}")
print(f"scatter_count: {scatter_count}")
print("------------------------------------------------------------------------------------")
print("Description: ")
print(f"Description given: {len(chart_list)-no_description_count}")
print(f"Average description length: {round(sum(description_len_list)/len(description_len_list), ndigits=1)}")
print("------------------------------------------------------------------------------------")
print("File types: ")
print(Counter(image_file_type))
print("------------------------------------------------------------------------------------")
print("Source: ")
print(f"Source given: {source_count}")
print("------------------------------------------------------------------------------------")
print("Wikipedia page usage: ")
print(f"Average Wikipedia page usage: {round(sum(wikipages_list_len)/len(wikipages_list_len), ndigits=1)}")
print("------------------------------------------------------------------------------------")
