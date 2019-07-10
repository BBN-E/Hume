import re

text_window = 14

increase_word = {"increase","increased","increasing"}
decrease_word = {"decrease","decreased","decreasing"}

trend_words = set(increase_word)
trend_words.update(decrease_word)


extend_able_modifier_wordset = {"large","nearly","over","","numbers"," ","many","most","smaller","majority","between","some","number","from","to",'per','cent','percent','each','daily','rate','%'}
extend_able_modifier_wordset.update(trend_words)

available_word_after_per = {"day","month","year"}

year_pattern = re.compile(r'^[12][09]\d\d$')

should_not_cross_word = {'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'}

number_str_to_multiplier = {
    "hundred":100,
    "thousand":1000,
    "million":1000000,
    "billion":1000000000,
    "hundreds":100,
    "thousands":1000,
    "millions":1000000,
    "billions":1000000000
}


words_to_add_estimation = set(number_str_to_multiplier.keys())

def my_tokenizer(sent_str):
    if isinstance(sent_str,unicode):
        sent_str = sent_str.encode('ascii','ignore')
    sent_str = sent_str.replace("("," ").replace(")"," ").replace("\n"," ")
    if len(sent_str) < 1:
        return list()
    if str.isalnum(sent_str[-1]) is False:
        sent_str = sent_str[0:-1]+" "
    tokens =  sent_str.split(" ")
    tokens =  [token[:-1] if token.endswith(",") else token for token in tokens]
    resolved_tokens = list()
    for token in tokens:
        if len(token) > 0:
            resolved_tokens.append(token)
    return resolved_tokens

def general_should_continue(token,status,text_window,should_not_cross_word):
    if abs(status['current_idx']-status['init_idx']) >= text_window:
        return False
    return True

def left_judger(token,status):
    if year_pattern.match(token):
        return False,{'continue':general_should_continue(token,status,text_window,should_not_cross_word)}
    for c in token:
        if c.isdigit():
            return True,{'continue':general_should_continue(token,status,text_window,should_not_cross_word)}
        elif c == "-":
            continue
        else:
            break
    if len(token) < 1:
        return False,{'continue':True}
    if token.lower() in extend_able_modifier_wordset:
        return True,{'continue':True}
    return False,{'continue':general_should_continue(token,status,text_window,should_not_cross_word)}

def extract_numeric_for_mention(sent_str,mention_str):
    mention_tokens = my_tokenizer(mention_str)
    tokens = my_tokenizer(sent_str)
    if len(mention_tokens) < 1 or len(tokens) < 1:
        return dict()
    start_mention_token_idx = -1
    end_mention_token_idx = -1
    for idx,token in reversed(list(enumerate(tokens))):
        if token == mention_tokens[0] and idx + len(mention_tokens) < len(tokens):
            if tokens[idx+len(mention_tokens)-1] == mention_tokens[-1]:
                start_mention_token_idx = idx
                end_mention_token_idx = idx + len(mention_tokens) - 1
                break

    if start_mention_token_idx == -1:
        return {
            # "min_val":None,
            # "val":None, # estimated value
            # "max_val":None,
            # "time_interval":None,
            # "trend":None
        }
    modifiers_idx_list = list()
    # Going left
    status = dict()
    for idx in range(start_mention_token_idx-1,-1,-1):
        status['current_idx'] = idx
        status['init_idx'] = start_mention_token_idx
        token = tokens[idx]
        if token in should_not_cross_word:
            continue
        if idx-1 >= 0 and tokens[idx-1] in should_not_cross_word:
            continue
        if idx-2 >= 0 and tokens[idx-2] in should_not_cross_word:
            continue
        if idx-3 >= 0 and tokens[idx-3] in should_not_cross_word:
            continue
        if idx +1 < len(tokens) and tokens[idx+1] in should_not_cross_word:
            continue
        if idx +2 < len(tokens) and tokens[idx+2] in should_not_cross_word:
            continue
        if idx +3 < len(tokens) and tokens[idx+3] in should_not_cross_word:
            continue
        current_is,status = left_judger(token,status)
        if current_is:
            modifiers_idx_list.append(idx)
        if status.get('continue',False) is False:
            break
    # Going right
    status = dict()
    for idx in range(end_mention_token_idx+1,len(tokens),1):
        status['current_idx'] = idx
        status['init_idx'] = end_mention_token_idx
        token = tokens[idx]
        if token in should_not_cross_word and str.isdigit(token.replace(",","")):
            continue
        if idx-1 >= 0 and tokens[idx-1] in should_not_cross_word:
            continue
        if idx-2 >= 0 and tokens[idx-2] in should_not_cross_word:
            continue
        if idx-3 >= 0 and tokens[idx-3] in should_not_cross_word:
            continue
        if idx +1 < len(tokens) and tokens[idx+1] in should_not_cross_word:
            continue
        if idx +2 < len(tokens) and tokens[idx+2] in should_not_cross_word:
            continue
        if idx +3 < len(tokens) and tokens[idx+3] in should_not_cross_word:
            continue
        current_is,status = left_judger(token,status)
        if current_is:
            modifiers_idx_list.append(idx)
        if status.get('continue',False) is False:
            break
    sol = dict()
    modifiers_idx_list = sorted(modifiers_idx_list)
    modifier_token = [tokens[idx].replace(",","") for idx in modifiers_idx_list]
    if len(trend_words.intersection(modifier_token)) > 0:
        sol['trend'] = "increase" if len(increase_word.intersection(modifier_token)) > 0 else "decrease"

    for idx,token in enumerate(tokens):
        if token in {"per","each"} and idx + 1 < len(tokens) and tokens[idx+1] in available_word_after_per:
            possible_val = None
            try:
                start_idx = modifier_token.index("each")
                for idx_2 in range(start_idx,-1,-1):
                    try:
                        possible_val = int(modifier_token[idx_2])
                    except:
                        pass
            except ValueError:
                pass
            if possible_val is None:
                try:
                    start_idx = modifier_token.index("per")
                    for idx_2 in range(start_idx,-1,-1):
                        try:
                            possible_val = int(modifier_token[idx_2])
                        except:
                            pass
                except ValueError:
                    pass
            if possible_val is not None:
                sol['time_interval'] = "{} {}".format(token,tokens[idx+1])
                sol['val'] = possible_val
                return sol
    if ("per" in modifier_token and "cent" in modifier_token) or "percent" in modifier_token or "%" in modifier_token:
        should_continue = True
        for token in modifier_token:
            try:
                i = int(token)
                if i > 100:
                    should_continue = False
            except:
                pass
        if should_continue is True:
            possible_rate = None
            for idx,token in enumerate(modifier_token):
                try:
                    possible_rate = float(token)
                    if idx+1 < len(modifier_token) and modifier_token[idx+1] in {"per","cent","percent","%"}:
                        break
                except:
                    pass
            if possible_rate != None:
                sol['val'] = possible_rate / 100
                return sol

    if ("between" in modifier_token) or (all({"from","to"}) in modifier_token):
        possible_values = list()
        possible_multiplier = 1
        for token in modifier_token:
            if token in number_str_to_multiplier:
                possible_multiplier = number_str_to_multiplier[token]
            try:
                possible_num = int(token)
                possible_values.append(possible_num)
            except:
                pass
        possible_values = sorted(possible_values)

        if len(possible_values) >= 2:
            sol['min_val'] = possible_values[0] * possible_multiplier
            sol['max_val'] = possible_values[-1] * possible_multiplier
            # Multiplier multiplier here
            return sol
    if "over" in modifier_token:
        possible_num = None
        possible_multiplier = 1
        for token in modifier_token:
            if token in number_str_to_multiplier:
                possible_multiplier = number_str_to_multiplier[token]
            try:
                possible_num = int(token)
            except:
                pass
        if possible_num is not None:
            sol['min_val'] = possible_num * possible_multiplier
            return sol

    modifier_token_set = set(modifier_token)
    if len(modifier_token_set.intersection(number_str_to_multiplier.keys())) > 1:
        possible_multiplier = 1
        possible_num = None
        for token in modifier_token:
            if token in number_str_to_multiplier:
                possible_multiplier = number_str_to_multiplier[token]
            try:
                possible_num = int(token)
            except:
                pass
        if possible_num is not None:
            sol['min_val']= possible_multiplier
            sol['val'] = 3 * possible_multiplier
            return sol
    possible_multiplier = 1
    possible_nums = set()
    for token in modifier_token:
        if token in number_str_to_multiplier:
            possible_multiplier = number_str_to_multiplier[token]
        try:
            possible_num = int(token)
            possible_nums.add(possible_num)
        except:
            pass
    if len(possible_nums) > 0:
        if len(possible_nums) > 1:
            sol['min_val'] = min(possible_nums) * possible_multiplier
            sol['max_val'] = max(possible_nums) * possible_multiplier
        else:
            sol['val'] = list(possible_nums)[0]
        return sol
    if (any(modifier_token) in {"number","amount","numbers"}):
        sol['val'] = "NA"
    return sol







if __name__ == "__main__":
    entries = [
        {"sent_str":"Since renewed fighting broke out across the country in July 2016, large numbers of refugees have poured into neighbouring countries, enlarging an already significant displacement crisis.","mention":"refugees","desired_modifiers":["large","numbers"]},
        {"sent_str":"By early-2017, nearly 60,000 people were fleeing the country each month, resulting in mass depopulation of both urban and rural areas.","mention":"people","desired_modifiers":["nearly", "60,000"]},
        {"sent_str":"In the first half of 2016, over 80,000 people left Greater Bahr el Ghazal for Sudan, due to drought, inflation and hunger.","mention":"people","desired_modifiers":["over","80000"]},
        {"sent_str":"More movement (10-30 people returning per day) was reported through Gangura and Nabiapai along the Yambio-Dungu road to the southeast of Yambio; insecurity is an issue along this road in DRC as well, but the market in Nabiapai reportedly still draws considerable traffic from DRC because it is larger than any other in the area.","mention":"returnees","desired_modifiers":["10-30","day"]},
        {"sent_str":"Along with those initially displaced from Yuai, the majority of these IDPs fled east towards Akobo Town, where reportedly between 10,000 and 30,000 IDPs arrived.","mention":"IDPs","desired_modifiers":["between","10,000","30,000"]},
        {"sent_str":"An average of 515 South Sudanese refugees arrived per day in Gambella.","mention":"South Sudanese",'desired_modifiers':['day','515']},
        {"sent_str":" Of the new arrivals, the majority (91 per cent) have entered through Pagak, while the remaining 9 per cent entered through Akobo.","mention":"arrivals","desired_modifiers":["91","per","cent","remaining","9"]},
        {"sent_str":"Between 1 and 15 March, over 10,000 South Sudanese refugees fled into Sudan, arriving in the border states of White Nile, South and West Kordofan and East Darfur at an average daily rate of nearly 690 refugees per day.","mention":"South Sudanese refugees","desired_modifiers":['daily',"rate","690"]},
        {"sent_str":" Cumulatively, Pamir is now home to 9,792 refugees since opening in September 2016.","mention":"refugees","desired_modifiers":["9,792"]}
    ]

    for entry in entries:
        print(extract_numeric_for_mention(entry['sent_str'],entry['mention']))
        print(entry['desired_modifiers'])
