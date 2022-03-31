import os,random,shutil,json
from hume_corpus import make_sgm_file,make_txt_file

def main():
    input_dir = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/covid/chinese_news_vol1.extracted"
    output_folder = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/covid/chinese_news_vol1_sgms/"
    shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    booking_arr = list()
    sgm_path_list = list()
    breaking_point = 10000
    for file in os.listdir(input_dir):
        with open(os.path.join(input_dir,file)) as fp:
            for i in fp:
                i = i.strip()
                crawl_en = json.loads(i)
                # print(crawl_en)
                # if "extracted_text" not in crawl_en:
                #     continue
                extracted_text = crawl_en["extracted_text"]
                doc_uuid = crawl_en["BBN_docid"]
                document_creation_time = crawl_en["BBN_website_creation_date"]
                source_uri = crawl_en["url"]
                author = crawl_en["BBN_website_name"]
                make_sgm_file(extracted_text, doc_uuid, output_folder,
                              "NON_CDR", source_uri,
                              "news_{}".format(doc_uuid), "CHS_NW_WM", document_creation_time, author, booking_arr,sgm_path_list, breaking_point)
                make_txt_file(extracted_text, doc_uuid, output_folder)



    with open(os.path.join(output_folder, "metadata.txt"), 'w') as wfp:
        for i in booking_arr:
            wfp.write("{}\n".format(i))
    random.shuffle(sgm_path_list)
    with open(os.path.join(output_folder, 'sgms.list'), 'w') as wfp:
        for i in sgm_path_list:
            wfp.write("{}\n".format(i))
    with open(os.path.join(output_folder, 'txts.list'), 'w') as wfp:
        for i in sgm_path_list:
            wfp.write("{}\n".format(i))

if __name__ == "__main__":
    main()