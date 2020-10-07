import os,sys,json,shutil,random
import datetime
import pandas
from hume_corpus import make_sgm_file,make_txt_file

def pdf_json_extractor(json_path):
    with open(json_path) as fp:
        j = json.load(fp)
    abstract = "\n".join(i['text'] for i in j["abstract"])
    body = "\n".join(i['text'] for i in j["body_text"])
    return "{}\n\n{}".format(abstract,body)

def pmc_json_extractor(json_path):
    with open(json_path) as fp:
        j = json.load(fp)
    if "abstract" in j:
        abstract = "\n".join(i['text'] for i in j["abstract"])
    else:
        abstract = ""
    body = "\n".join(i['text'] for i in j["body_text"])
    return "{}\n\n{}".format(abstract,body)


def main():
    data_root = "/nfs/raid88/u10/data/cord-19"
    output_folder = "/nfs/raid88/u10/users/hqiu/raw_corpus/cord_19"
    shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    booking_arr = list()
    sgm_path_list = list()
    breaking_point = 10000
    metadata = os.path.join(data_root,'metadata.csv')

    df = pandas.read_csv(metadata)

    headers = list(df)

    for idx, row in df.iterrows():
        doc_uuid = row["cord_uid"]
        author = "UNKNOWN"
        if pandas.isna(row["authors"]) is False:
            author = row["authors"]
        title = row["title"]
        creation_date_str = "UNKNOWN"
        if pandas.isna(row["publish_time"]) is False:
            if row["publish_time"].count("-") == 2:
                creation_date = datetime.datetime.strptime(row["publish_time"], '%Y-%m-%d')
                creation_date_str = creation_date.strftime("%Y%m%d")
            elif row["publish_time"].count("-") == 0:
                creation_date = datetime.datetime.strptime(row["publish_time"], '%Y')
                creation_date_str = creation_date.strftime("%Y%m%d")
        if pandas.isna(row["pdf_json_files"]):
            pdf_json_file_path = ""
        else:
            pdf_json_file_path = os.path.join(data_root,row["pdf_json_files"])
        if pandas.isna(row["pmc_json_files"]):
            pmc_json_file_path = ""
        else:
            pmc_json_file_path = os.path.join(data_root,row["pmc_json_files"])

        extracted_text = ""
        source_uri = ""
        if os.path.exists(pdf_json_file_path):
            extracted_text = pdf_json_extractor(pdf_json_file_path)
            source_uri = pdf_json_file_path

        elif os.path.exists(pmc_json_file_path):
            extracted_text = pmc_json_extractor(pmc_json_file_path)
            source_uri = pmc_json_file_path

        if len(extracted_text) > 0:
            make_sgm_file(extracted_text, doc_uuid, output_folder,
                          "NON_CDR", source_uri,
                          "analytic_{}".format(doc_uuid), "ENG_NW_WM", creation_date_str, author, booking_arr,
                          sgm_path_list, breaking_point)
            make_txt_file(extracted_text, doc_uuid, output_folder)
    with open(os.path.join(output_folder,"metadata.txt"),'w') as wfp:
        for i in booking_arr:
            wfp.write("{}\n".format(i))
    random.shuffle(sgm_path_list)
    with open(os.path.join(output_folder,'sgms.list'),'w') as wfp:
        for i in sgm_path_list:
            wfp.write("{}\n".format(i))


if __name__ == "__main__":
    main()