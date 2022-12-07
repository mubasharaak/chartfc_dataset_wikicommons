import json
import csv
import pymongo
import json
from pymongo import InsertOne
import certifi

PATH_MONGODB_CREDENTIALS = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\config\mongodb_credentials.json"


def dataset_json_to_csv(json_file_path: str):
    """
    Converts json dataset file to csv
    :param json_file_path: path to dataset file
    :return: None (file is saved as .csv using json_file_path as location)
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    # now we will open a file for writing
    data_file = open(json_file_path.split(".json")[0]+".csv", 'w')
    csv_writer = csv.writer(data_file)

    count = 0
    for entry in dataset[0]:
        if count == 0:
            # Writing headers of CSV file
            header = entry.keys()
            csv_writer.writerow(header)
            count += 1

        # Writing data of CSV file
        csv_writer.writerow(entry.values())


def upload_json_mongodb(json_file_path: str, db_name: str, db_collection_name: str):
    """
    Load chartfc data collected from Wikimedia commons into MongoDB db db_name (e.g. "chartfc") collection db_collection_name (e.g. "chart_filtering")

    :param json_file_path:
    :param db_name:
    :param db_collection_name:
    :return:
    """
    with open(PATH_MONGODB_CREDENTIALS, 'r') as f:
        mongodb_credentials = json.load(f)

    # Connect to Mong\oDB
    client = pymongo.MongoClient(mongodb_credentials["connection_string"],
                                    tlsCAFile=certifi.where())  # connecting to database
    db = client[db_name]
    collection = db[db_collection_name]

    with open(json_file_path) as f:
        data = json.load(f)

    requesting = [InsertOne(jsonObj) for jsonObj in data[0]]
    collection.bulk_write(requesting)
    client.close()


def load_wikimedia_data_mongodb():
    """
    Loads all chart dataset files created from Wikimedia commons into Mongodb DB "chartfc"
    :return:
    """
    path = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\init_dataset\line_chart.json"
    upload_json_mongodb(path, "chartfc", "chart_filtering")

    path = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\init_dataset\barchart_horizontal.json"
    upload_json_mongodb(path, "chartfc", "chart_filtering")

    path = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\init_dataset\barchart_vertical.json"
    upload_json_mongodb(path, "chartfc", "chart_filtering")

    path = r"C:\Users\k20116188\PycharmProjects\chartfc_dataset_wikicommons\data\init_dataset\pie_chart.json"
    upload_json_mongodb(path, "chartfc", "chart_filtering")


if __name__ == '__main__':
    load_wikimedia_data_mongodb()
