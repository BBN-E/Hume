import os,sys,json,collections,datetime

YearMonthEntry = collections.namedtuple('YearMonthEntry',['year','month','day'])

def divide_in_bucket(input_json_arr):
    sorting_dict = dict()
    for i in input_json_arr:
        try:
            d = datetime.datetime.utcfromtimestamp(i['unixtimestamp']/1000)
            sorting_dict.setdefault(d.year,dict()).setdefault(d.month,list()).append(i)
        except ValueError:
            # print("skip entry with unixtimestamp: " + str(i['unixtimestamp']))
            continue
    ret_bucket_arr = list()
    for year in sorted(sorting_dict.keys()):
        year_buf = list()
        for month in sorted(sorting_dict[year].keys()):
            month_buf = sorted(sorting_dict[year][month],key=lambda x:x['unixtimestamp'])
            year_buf.append(month_buf)
        ret_bucket_arr.append(year_buf)
    return ret_bucket_arr

# {
# "@class":".DumpEventMentionForEventTimeline$EventMentionWithTime",
# "docId":"ENG_NW_20090105_M3SS4_0008_0",
# "sentStart":1824,
# "sentEnd":2013,
# "anchorStart":1985,
# "anchorEnd":1988,
# "sentStr":"The United Nations - Afri
# can Union Mission in Darfur -LRB- UNAMID -RRB- was established in July 2007 , but the peacekeeping force has struggled to secure the region due to a lack of troops and equipment .",
# "anchorStr":"lack",
# "eventType":"factor_001",
# "unixtimestamp":1183262400000,
# "arguments":
# [
# {
# "@class":".DumpEventMentionForEventTimeline$EventArgumentEntry",
# "type":"located_at",
# "originalText":"the region",
# "canonicalText":"Republic of the Sudan"
# },
# {
# "@class":".DumpEventMentionForEventTimeline$EventArgumentEntry",
# "type":"DestinationLocation",
# "originalText":"the region",
# "canonicalText":"Republic of the Sudan"}]}

def deduplicate_list(mylist):
    newlist = []
    for i in mylist:
        if i not in newlist:
            newlist.append(i)
    return newlist

def get_arg_text(canonicalText, originalText):
    if canonicalText == "UNKNOWN-ACTOR":
        canonicalText = ""

    if canonicalText!="":
        return canonicalText
    else:
        return originalText

def print_event_string(year, month, entry):
    docId = entry["docId"]
    sentStr = entry["sentStr"].replace("\n", "").replace("\t", " ")
    anchorStr = entry["anchorStr"]
    eventType = entry["eventType"]

    if eventType == "Generic":
        return

    unixtimestamp = entry["unixtimestamp"]

    args = []

    actors = []
    locations = []
    instruments_goods_or_property = []

    located_at = ""
    has_active_actor = ""
    has_affected_actor = ""
    has_actor = ""
    SourceLocation = ""
    DestinationLocation = ""
    has_origin = ""
    has_destination = ""
    has_instrument = ""
    involves_goods_or_property = ""

    for argument in entry["arguments"]:
        role = argument["type"]
        originalText = argument["originalText"]
        canonicalText = argument["canonicalText"]
        args.append((role, originalText, canonicalText))

        #if canonicalText == "UNKNOWN-ACTOR":
        #    continue

        if role == "located_at":
            located_at = get_arg_text(canonicalText, originalText)
            # print ("located_at:\t" + canonicalText + "|" + originalText + "|" + located_at)
            if located_at != "":
                locations.append(located_at)
        if role == "has_active_actor":
            has_active_actor = get_arg_text(canonicalText, originalText)
            if has_active_actor != "":
                actors.append(has_active_actor)
        if role == "has_affected_actor":
            has_affected_actor = get_arg_text(canonicalText, originalText)
            if has_affected_actor != "":
                actors.append(has_affected_actor)
        if role == "has_actor":
            has_actor = get_arg_text(canonicalText, originalText)
            if has_actor != "":
                actors.append(has_actor)
        if role == "SourceLocation":
            SourceLocation = get_arg_text(canonicalText, originalText)
            if SourceLocation != "":
                locations.append(SourceLocation)
        if role == "DestinationLocation":
            DestinationLocation = get_arg_text(canonicalText, originalText)
            if DestinationLocation != "":
                locations.append(DestinationLocation)
        if role == "has_origin":
            has_origin = get_arg_text(canonicalText, originalText)
            if has_origin != "":
                locations.append(has_origin)
        if role == "has_destination":
            has_destination = get_arg_text(canonicalText, originalText)
            if has_destination != "":
                locations.append(has_destination)
        if role == "has_instrument" != "":
            has_instrument = get_arg_text(canonicalText, originalText)
            if has_instrument != "":
                instruments_goods_or_property.append(has_instrument)
        if role == "involves_goods_or_property":
            involves_goods_or_property = get_arg_text(canonicalText, originalText)
            if involves_goods_or_property != "":
                instruments_goods_or_property.append(involves_goods_or_property)

    locations = deduplicate_list(locations)
    actors = deduplicate_list(actors)
    instruments_goods_or_property = deduplicate_list(instruments_goods_or_property)

    print("EVENT\t" + str(year) + "\t" + str(month) +
          "\t" + eventType + "\t" + anchorStr +
          "\t" + ';'.join(locations) +
          "\t" + ';'.join(actors) + "\t" + ';'.join(instruments_goods_or_property) +
          "\t" + sentStr)
    # "\t" + SourceLocation + "\t" + DestinationLocation + "\t" + has_origin + "\t" + has_destination
          # "\t" + has_active_actor + "\t" + has_affected_actor + "\t" + has_actor +
          # + "\t" + has_instrument + "\t" + involves_goods_or_property +

def main(input_ljson_file):
    input_json_arr = list()
    with open(input_ljson_file,'r') as fp:
        for i in fp:
            i = i.strip()
            input_json_arr.append(json.loads(i))

    # print("EVENT\tyear\tmonth\teventType\tanchorStr\tlocated_at\thas_active_actor\thas_affected_actor\thas_actor\tSourceLocation\tDestinationLocation\thas_origin\thas_destination\thas_instrument\tinvolves_goods_or_property\tsentStr")
    print("EVENT\tyear\tmonth\teventType\tanchorStr\tlocated_at\thas_actor\tinstruments_goods_or_property\tsentStr")

    ret = divide_in_bucket(input_json_arr)
    for sorted_year in ret:
        for sorted_month in sorted_year:
            for entry in sorted_month:
                d = datetime.datetime.utcfromtimestamp(entry['unixtimestamp']/1000)
                # print(str(d.year) + "\t" + str(d.month))
                # print(str(entry))
                if d.year >= 2011 and d.year <= 2017:
                    print_event_string(d.year, d.month, entry)

if __name__ == "__main__":
    # input_ljson_file = "/home/hqiu/massive/tmp/test.ljson"
    if len(sys.argv) != 2:
        print("Usage: input-ljson")
        sys.exit(-1)
    input_ljson_file = sys.argv[1]
    main(input_ljson_file)
