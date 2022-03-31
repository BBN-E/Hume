import datetime
import json
import re
import requests
import logging

logger = logging.getLogger(__name__)

def easy_day_time_getter(regex_match):
    return datetime.datetime.utcfromtimestamp(int(regex_match[0][0])/100000000)

def tom_com_time_getter(regex_match):
    year,month = int(regex_match[0][0]),int(regex_match[0][1])
    return datetime.datetime(year,month,2)

website_data_list = [
    # {"name":"eastday.com","main_search":"*.eastday.com/*","post_url_regex":re.compile(r"https?:\/\/*.+\.eastday\.com\/pnews\/(\d+)"),"time_getter":easy_day_time_getter}
    # {"name":"163","main_search":"www.163.com/news/article/*","rough_url_regex":re.compile(r"https?:\/\/www\.163\.com\/news\/article/")},
    # {"name":"voachinese.com","main_search":"www.voachinese.com/*","post_url_regex":re.compile(r"https?:\/\/www\.voachinese.com\/*.+-(\d{4})-(\d{2})-(\d{2})\/\d+.html")}


    # {"name":"ifeng","main_search":"news.ifeng.com/*","post_url_regex":None,"rough_url_regex":re.compile(r"https?:\/\/news\.ifeng\.com\/[A-Za-z0-9]+\/[A-Za-z0-9]+")},
    # {"name":"thenewslens","main_search":"www.thenewslens.com/article/*","post_url_regex":None,"rough_url_regex":re.compile(r"https?:\/\/www.thenewslens.com\/article/\d+")}

    {"name": "sina", "main_search": "*.news.sina.com.cn/*","post_url_regex": re.compile(r"https?:\/\/*.+.?news\.sina\.com\.cn\/*.+\/(\d{4})-(\d{2})-(\d{2})\/*.+")},
    {"name":"people.com.cn","main_search":"*.people.com.cn","post_url_regex":re.compile(r"https?://*.+\.people\.com\.cn/*.+/(\d{4})/(\d{2})(\d{2})/*.+\.html")},
    {"name":"xinhuanet","main_search":"www.xinhuanet.com/*","post_url_regex":re.compile(r"https?://www\.xinhuanet\.com/*.+/(\d{4})-(\d{2})/(\d{2})/*.+\.htm")},
    {"name":"zaobao","main_search":"https://www.zaobao.com.sg/*","post_url_regex":re.compile(r"https?://www\.zaobao\.com\.sg/*.+/story(\d{4})(\d{2})(\d{2})-\d+")},
    {"name":"cnnytimes","main_search":"https://cn.nytimes.com/*","post_url_regex":re.compile(r"https?://cn\.nytimes\.com/*.+/(\d{4})(\d{2})(\d{2})/*.+")},
    {"name":"chinadaily","main_search":"cn.chinadaily.com.cn/*","post_url_regex":re.compile(r"https?:\/\/cn\.chinadaily\.com\.cn\/[A-Za-z0-9]+\/(\d{4})(\d{2})\/(\d{2})\/*.+html")},
    {"name":"jrj.com.cn","main_search":"*.jrj.com.cn/*","post_url_regex":re.compile(r"https?:\/\/*.+\.jrj\.com\.cn\/(\d{4})\/(\d{2})\/(\d{2})\d+\.shtml")},
    {"name":"cctv.com","main_search":"news.cctv.com/*","post_url_regex":re.compile(r"https?:\/\/news.cctv.com\/(\d{4})/(\d{2})/(\d{2})/*.+")},
    {"name":"news.tom.com","main_search":"news.tom.com/*","post_url_regex":re.compile(r"https?:\/\/news\.tom\.com\/(\d{4})(\d{2})/\d+\.html"),"time_getter":tom_com_time_getter},
    {"name":"epochtime","main_search":"www.epochtimes.com/gb/*","post_url_regex":re.compile(r"https?:\/\/www.epochtimes.com\/gb\/(\d{2})\/(\d{1,2})\/(\d{1,2})\/n\d+.htm")},
    {"name":"china.com","main_search":"*.china.com/*","post_url_regex":re.compile(r"https?:\/\/*.+\.china\.com/*.+news*.+/\d+/(\d{4})(\d{2})(\d{2})/\d+.html")},
    {"name":"china.com.cn","main_search":"news.china.com.cn/*","post_url_regex":re.compile(r"https?:\/\/news\.china\.com\.cn\/(\d{4})-(\d{2})/(\d{2})\/content_\d+.htm")},
    {"name":"guancha.cn","main_search":"www.guancha.cn/*","post_url_regex":re.compile(r"https?:\/\/www\.guancha\.cn\/*.+\/(\d{4})_(\d{2})_(\d{2})_\d+.shtml")}

]

care_volumes = {
    "CC-MAIN-2019-51",
    "CC-MAIN-2020-05",
    "CC-MAIN-2020-10",
    "CC-MAIN-2020-16",
    "CC-MAIN-2020-24",
    "CC-MAIN-2020-29",
    "CC-MAIN-2020-34",
    "CC-MAIN-2020-40"
}


def get_relevant_warc_path(index_suffix, target_urls):
    """
    @hqiu For why we can do this, https://commoncrawl.org/the-data/get-started/ and search for `URL and metadata indexes`
    :param index_suffix:
    :param target_urls:
    :return:
    """
    base_url = "https://index.commoncrawl.org/"
    legit_metadata_list = list()
    date_cnt = dict()
    counter = 0

    with requests.session() as session:
        for target_url in target_urls:
            # Two stages. Stage 1, get number of pages
            p = {
                "url": target_url['main_search'], "showNumPages": "true"
            }
            if target_url.get("rough_url_regex", None) is not None:
                p["filter"] = "~url:{}".format(target_url["rough_url_regex"].pattern)
            if target_url.get("post_url_regex",None) is not None:
                p["filter"] = "~url:{}".format(target_url["post_url_regex"].pattern)
            response = session.get("{}{}-index".format(base_url, index_suffix),params=p)
            if response.status_code >= 400:
                logger.error("Error accessing {}".format("{}{}-index".format(base_url, index_suffix)))
                continue
            resp_meta = response.json()
            logger.info(resp_meta)
            number_of_pages = resp_meta["pages"]
            page_size = resp_meta["pageSize"]

            for page_idx in range(number_of_pages):
                p = {
                    "url": target_url['main_search'], "pageSize": page_size,
                    "page": page_idx
                }
                if target_url.get("rough_url_regex",None) is not None:
                    p["filter"] = "~url:{}".format(target_url["rough_url_regex"].pattern)
                if target_url.get("post_url_regex", None) is not None:
                    p["filter"] = "~url:{}".format(target_url["post_url_regex"].pattern)
                response = session.get("{}{}-index".format(base_url, index_suffix),
                                       params=p)
                if response.status_code < 400:
                    for line in response.content.splitlines():
                        url_pattern, timestamp, *rest = line.decode("utf-8").split(" ")
                        record = " ".join(rest)
                        record = json.loads(record)
                        crawled_status_code = int(record["status"])
                        if crawled_status_code >= 300:
                            continue
                        crawled_url = record["url"]
                        crawl_file_name = record["filename"]
                        # if "languages" not in record.keys():
                        #     continue
                        # languages = set(record['languages'].split(","))
                        # if "zho" not in languages:
                        #     continue
                        if target_url.get("post_url_regex",None) is not None:
                            date_regex_match = target_url["post_url_regex"].findall(crawled_url)
                            if "time_getter" in target_url:
                                try:
                                    d = target_url["time_getter"](date_regex_match)
                                except ValueError as e:
                                    logger.exception("Status: {}".format(response.status_code))
                                    logger.exception("Error handling {}".format(p))
                                    continue
                            else:
                                if len(date_regex_match) > 0:
                                    try:
                                        d = datetime.datetime(int(date_regex_match[0][0]), int(date_regex_match[0][1]),
                                                              int(date_regex_match[0][2]))
                                    except ValueError as e:
                                        logger.exception("Status: {}".format(response.status_code))
                                        logger.exception("Error handling {}".format(p))
                                        continue
                                else:
                                    logger.exception("Status: {}".format(response.status_code))
                                    logger.exception("Error handling {}".format(p))
                                    continue

                            if (d.year, d.month) in {(2019, 12), (2020, 1), (2020, 2), (2020, 3), (2020, 4),
                                                     (2020, 5), (2020, 6), (2020, 7)}:
                                record["BBN_website_name"] = target_url['name']
                                record["BBN_website_creation_date"] = d.strftime("%Y%m%d")
                                legit_metadata_list.append(record)
                                date_cnt[(d.year, d.month)] = date_cnt.get((d.year, d.month), 0) + 1

                        else:
                            record["BBN_website_name"] = target_url['name']
                            record["BBN_website_creation_date"] = None
                            legit_metadata_list.append(record)
                            date_cnt[("UNKNOWN","UNKNOWN")] = date_cnt.get(("UNKNOWN","UNKNOWN"), 0) + 1
                else:
                    logger.exception("Status: {}".format(response.status_code))
                    logger.exception("Error handling {}".format(p))
    return legit_metadata_list, date_cnt


def main():
    record_filename_to_crawling_jobs = dict()
    aggr_date_cnt = dict()
    for care_volume in care_volumes:
        logger.info("Handling {}".format(care_volume))
        legit_metadata_list, date_cnt = get_relevant_warc_path(care_volume, website_data_list)
        for en in legit_metadata_list:
            record_filename_to_crawling_jobs.setdefault(en["filename"], list()).append(en)
        for (year, month), cnt in date_cnt.items():
            aggr_date_cnt[(year, month)] = aggr_date_cnt.get((year, month), 0) + cnt
        logger.info(aggr_date_cnt)
        logger.info("Finished {}".format(care_volume))
        with open("/home/hqiu/wait_for_crawling.json", 'w') as wfp:
            json.dump(record_filename_to_crawling_jobs, wfp, indent=4, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
