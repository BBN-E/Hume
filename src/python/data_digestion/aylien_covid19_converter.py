import os,sys,shutil,json,random
from hume_corpus import make_sgm_file,make_txt_file


def main():
    f_path = "/nfs/raid88/u10/users/bmin/projects/cord19/datasets/aylien_covid_news_data.jsonl"
    output_folder = "/nfs/raid88/u10/users/hqiu/raw_corpus/aylien_covid19"
    shutil.rmtree(output_folder,ignore_errors=True)
    os.makedirs(output_folder,exist_ok=True)
    booking_arr = list()
    sgm_path_list = list()
    breaking_point = 10000
    with open(f_path) as fp:
        for idx,i in enumerate(fp):
            i = i.strip()
            j = json.loads(i)
            author = j.get("author",dict()).get("name","UNKNOWN").replace("\t"," ").replace("\n"," ")
            if len(author.strip()) < 1:
                author = "UNKNOWN"
            extracted_text = j.get("body","")
            docid = "aylien_{}".format(j['id'])
            creation_date = "UNKNOWN"
            if j.get("published_at",None) is not None:
                creation_date = j['published_at'].split(" ")[0].replace("-","")
            source_uri = j.get("links",dict()).get("permalink","UNKNOWN").replace("\t"," ").replace("\n"," ")
            if len(source_uri.strip()) < 1:
                source_uri = "UNKNOWN"
            if len(extracted_text) > 0:
                make_sgm_file(extracted_text, docid, output_folder,
                              "NON_CDR", source_uri,
                              "news_{}".format(docid), "ENG_NW_WM", creation_date, author, booking_arr,
                              sgm_path_list, breaking_point)
            if idx % 1000 == 0:
                print("Processed {}".format(idx))
    with open(os.path.join(output_folder, "metadata.txt"), 'w') as wfp:
        for i in booking_arr:
            wfp.write("{}\n".format(i))
    random.shuffle(sgm_path_list)
    with open(os.path.join(output_folder, 'sgms.list'), 'w') as wfp:
        for i in sgm_path_list:
            wfp.write("{}\n".format(i))

if __name__ == "__main__":
    main()