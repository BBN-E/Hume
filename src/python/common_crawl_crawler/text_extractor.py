import json
import logging
import lxml.html
import traceback
import multiprocessing
import multiprocessing.managers
import io
from bs4 import BeautifulSoup

# https://stackoverflow.com/a/50878600/6254393
# Backup original AutoProxy function
backup_autoproxy = multiprocessing.managers.AutoProxy

# Defining a new AutoProxy that handles unwanted key argument 'manager_owned'
def redefined_autoproxy(token, serializer, manager=None, authkey=None,
          exposed=None, incref=True, manager_owned=True):
    # Calling original AutoProxy without the unwanted key argument
    return backup_autoproxy(token, serializer, manager, authkey,
                     exposed, incref)

# Updating AutoProxy definition in multiprocessing.managers package
multiprocessing.managers.AutoProxy = redefined_autoproxy

logger = logging.getLogger(__name__)

def text_stripper(original_text):
    return "\n".join(filter(lambda x: len(x) > 0, map(lambda x: x.strip(), original_text.splitlines())))

class MainContentExtractor(object):
    def __init__(self):
        pass

    def extract(self,original_json_en):
        pass

class SinaExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")

            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".main-title"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".date-source"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                for candidate_class in {"#article"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_content = candidate.get_text()
                        break
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class PeopleExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")

            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {"h1"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".fl"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_meta is None:
                candidate = "\n".join(j.get_text() for j in soup.select(".sou"))
                if len(candidate) > 0:
                    article_meta = candidate
            if article_content is None:
                candidate = "\n".join(j.get_text() for j in soup.select("p[style='text-indent: 2em;']"))
                if len(candidate) > 0:
                    article_content = candidate
            if article_content is None:
                candidate = "\n".join(j.get_text() for j in soup.select(".text_con p"))
                if len(candidate) > 0:
                    article_content = candidate
            if article_content is None:
                for candidate_class in {".content"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_content = candidate.get_text()
                        break
            if article_title is None or article_meta is None or article_content is None:
                print(soup)
                print(article_title)
                print(article_meta)
                print(article_content)
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class XinhuanetExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff,"lxml",from_encoding="utf-8")

            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".h-title",".p-title","#title","h1"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".h-info",".p-info",".info",".source"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                for candidate_class in {".h-detail","#p-detail","#content",".content"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_content = candidate.get_text()
                        break
            if article_title is None or article_meta is None or article_content is None:
            #     print(soup)
            #     print(article_title)
            #     print(article_meta)
            #     print(article_content)
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            return "{}\n{}\n{}\n".format(processed_title,processed_meta,processed_content)

class ZaobaoExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff,"lxml",from_encoding="utf-8")
            article_title = soup.select_one(".article-title").get_text()
            article_meta = soup.select_one(".article-meta").get_text()
            article_content = soup.select_one(".article-content").get_text()
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            return "{}\n{}\n{}\n".format(processed_title,processed_meta,processed_content)

class CNNYTimeExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")

            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".article-header h1"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".byline"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".article-paragraph"))
            if article_title is None or article_meta is None or article_content is None:
                # print(soup)
                # print(article_title)
                # print(article_meta)
                # print(article_content)
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class JRJExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".titmain h1"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".inftop span"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".texttit_m1"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)


class CCTVExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".title_area h1"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".title_area .info"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".content_area"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class TOMExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".news_box_title"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".infor_time"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".news_box_text"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class EpochtimeExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".title"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".info time"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".post_content"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class ChinaCOMExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".article_title"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".article_info .time"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".article_content"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class ChinaCOMCNExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".articleTitle"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {"#pubtime_baidu"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select("#articleBody"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

class GuanchaExtractor(MainContentExtractor):
    def extract(self,original_json_en):
        with io.BytesIO() as io_buff:
            io_buff.write(original_json_en['original_html'].encode("utf-8"))
            io_buff.seek(0)
            soup = BeautifulSoup(io_buff, "lxml",from_encoding="utf-8")
            article_title = None
            article_meta = None
            article_content = None
            if article_title is None:
                for candidate_class in {".left-main h3"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_title = candidate.get_text()
                        break
            if article_meta is None:
                for candidate_class in {".time span"}:
                    candidate = soup.select_one(candidate_class)
                    if candidate is not None:
                        article_meta = candidate.get_text()
                        break
            if article_content is None:
                article_content = "\n".join(j.get_text() for j in soup.select(".all-txt"))
            if article_title is None or article_meta is None or article_content is None:
                if article_title is None:
                    article_title = ""
                if article_meta is None:
                    article_meta = ""
            processed_title = text_stripper(article_title)
            processed_meta = text_stripper(article_meta)
            processed_content = text_stripper(article_content)
            # print("Extracted")
            # print("{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content))
            return "{}\n{}\n{}\n".format(processed_title, processed_meta, processed_content)

def mapper(job_queue,output_queue):
    extractor_factory = {
        "sina":SinaExtractor(),
        "people.com.cn":PeopleExtractor(),
        "xinhuanet":XinhuanetExtractor(),
        "zaobao":ZaobaoExtractor(),
        "cnnytimes":CNNYTimeExtractor(),
        "jrj.com.cn":JRJExtractor(),
        "cctv.com":CCTVExtractor(),
        "news.tom.com":TOMExtractor(),
        "epochtime":EpochtimeExtractor(),
        "china.com":ChinaCOMExtractor(),
        "china.com.cn":ChinaCOMCNExtractor(),
        "guancha.cn": GuanchaExtractor()
    }

    while True:
        job_en = job_queue.get()
        if job_en is None:
            break
        original_json_en = json.loads(job_en)
        source = original_json_en["BBN_website_name"]
        if source not in extractor_factory:
            logger.warning("Skipping {}".format(source))
            continue
        try:
            extracted_text = extractor_factory[source].extract(original_json_en)
            original_json_en["extracted_text"] = extracted_text
            output_queue.put(original_json_en)
        except Exception as e:
            logger.exception(traceback.format_exc())
    output_queue.put(None)

def reducer(output_queue,n_workers,output_path):
    stop_signals_received = 0
    with open(output_path,'w') as wfp:
        while True:
            elem = output_queue.get()
            if elem is None:
                stop_signals_received += 1
                if stop_signals_received >= n_workers:
                    break
            else:
                wfp.write("{}\n".format(json.dumps(elem,ensure_ascii=False)))
            # if elem['BBN_website_name'] not in {"zaobao","xinhuanet","sina","cnnytimes"}:
            #     print(elem['BBN_website_name'] ,elem['extracted_text'])

def main(input_corpus_dump,output_path):
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    output_queue = manager.Queue()
    n_workers = multiprocessing.cpu_count()
    # n_workers = 1

    converted_doc_cnt = 0
    with open(input_corpus_dump) as fp, manager.Pool(n_workers+1) as pool:
        for i in fp:
            i = i.strip()
            job_queue.put(i)
            converted_doc_cnt+= 1
            # if converted_doc_cnt > 2000:
            #     break
        workers = list()
        # Step 2 put in end job markings
        for _ in range(n_workers):
            job_queue.put(None)
        # Step 3 spawn mappers
        for _ in range(n_workers):
            proc = pool.apply_async(mapper, args=(job_queue,output_queue,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(reducer,args=(output_queue,n_workers,output_path,))
        workers.append(proc)
        for worker in workers:
            worker.wait()

if __name__ == "__main__":
    for i in range(8):
        input_corpus_dump = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/covid/chinese_news_vol2/commoncrawl_dump_{}".format(i)
        output_path = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/covid/chinese_news_vol2.extracted/commoncrawl_dump_{}".format(i)
        main(input_corpus_dump, output_path)
