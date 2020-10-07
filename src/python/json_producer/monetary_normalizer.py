# -*- coding: utf-8 -*-

import re

## 
## TODO: Expand list of currencies and regexes
##
## This was a quick effort to catch 95%+ of cases in the Month 5
## corpus. If we switch corpora, we'll need to fill out this 
## capability so it is more comprehensive.
##

currencies = {
    "dollars": "UnitedStatesDollar",
    "$": "UnitedStatesDollar",
    "us dollars": "UnitedStatesDollar",
    "us$": "UnitedStatesDollar",
    "us $": "UnitedStatesDollar",
    "u.s.$": "UnitedStatesDollar",
    "usd": "UnitedStatesDollar",
    "n": "NigeriaNaira",
    "naira": "NigeriaNaira",
    "euros": "Euro",
    "rand": "SouthAfricaRand",
    "cfa franc": "CFAFranc",
    "cfa francs": "CFAFranc",
    "£": "UnitedKingdomPound",
    "hk$": "HongKongDollar",
    "hk $": "HongKongDollar",
}

def lookup_currency(currency_indicator):
    l = currency_indicator.lower()
    return currencies.get(l)

small_numbers = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
    "nineteen": "19", "twenty": "20", "thirty": "30", "forty": "40",
    "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80",
    "ninety": "90"
    }
    

amount = r"([\d,]+\.?\d*)"
plural_numeric_words = r"(hundreds|thousands|millions|billions|trillions|hundreds of millions|hundreds of billions|tens of millions|tens of billions)"
numeric_words = r"(hundred|thousand|million|billion|trillion|bn|b|m|mm)"
currency_words = r"(dollars|euros|naira|rand|us dollars|us\$|us \$|usd)"
currency_indicators = r"(\$|n|us\$|us \$|usd|u.s.\$|£|hk\$|hk \$)"
minimum_modifiers = r"(over|more than|greater than|no less than|at least|above)"
maximum_modifiers = r"(up to|as much as|under|less than|no more than|at most|nearly|near|almost|below)"
unclear_modifiers = r"(about|approx\.|approximately|around|close to|near|estimated|rough|roughly)"
between_words = r"(between|in between)"

irrelevant_prefixes = ["only", "an additional", "another", "additional", "just ", "-", "the ", "an ", "a ", "some "]
irrelevant_suffixes = ["/", "(", ")"]

whitespace_re = re.compile(r"\s+")

minimum_mod_re = re.compile(r"^" + minimum_modifiers + r"\s*", re.I)
maximum_mod_re = re.compile(r"^" + maximum_modifiers + r"\s*", re.I)
unclear_mod_re = re.compile(r"^" + unclear_modifiers + r"\s*", re.I)

# billions of dollars
r1 = re.compile(plural_numeric_words + r" of " + currency_words + r"$", re.I)
# $10 billion
r2 = re.compile(currency_indicators + r"\s?" + amount + r"\-?\s?" + numeric_words + r"$", re.I)
# $14
r3 = re.compile(currency_indicators + r"\s?" + amount + r"$", re.I)
# 2 dollars
r8 = re.compile(amount + r" " + currency_words + "$", re.I)
# 4.95 trillion naira
r9 = re.compile(amount + r"\s?" + numeric_words + r" " + currency_words + r"$", re.I)
# more than 4,500 rand
r11 = re.compile(currency_indicators + amount + numeric_words + r"$", re.I)
# $5 million dollars
r12 = re.compile(currency_indicators + amount + r"\s?" + numeric_words + r" " + currency_words + r"$", re.I)
# $US
r13 = re.compile(currency_indicators + r"$", re.I)
# $US thousand
r14 = re.compile(currency_indicators + r"\s?" + numeric_words + r"$", re.I)
# between $2 and $5
r15 = re.compile(between_words + "? ?" + currency_indicators + amount + r" ?(and|to|\-) ?" + currency_indicators + "?" + amount + r"$", re.I)
# between $2 million and $5 million
r16 = re.compile(between_words + "? ?" + currency_indicators + amount + r"\s?" + numeric_words + r" ?(and|to|\-) ?" + currency_indicators + "?" + amount + r"\s?" + numeric_words + "$", re.I)
# several millions of naira
r17 = re.compile("(several)" + " " + plural_numeric_words + r" of " + currency_words + r"$", re.I)
# between $1 and 5 million
r18 = re.compile(between_words + "? ?" + currency_indicators + "\s?" + amount + r" ?(and|to|\-) ?" + currency_indicators + "?" + amount + "\s?" + numeric_words + r"$", re.I)
# between 300 to 400 naira
r19 = re.compile(between_words + "? ?" + amount + r" ?(and|to|\-) ?" + amount + r"\s?" + currency_words + r"$", re.I)

def word_to_number(w):
    if w is None:
        return 1

    w = w.lower()
    if w == "hundred" or w == "hundreds":
        return 100
    if w == "thousand" or w == "thousands":
        return 1000
    if w == "million" or w == "millions" or w == "m" or w == "mm":
        return 1000000
    if w == "billion" or w == "billions" or w == "bn" or w == "b":
        return 1000000000
    if w == "trillion" or w == "trillions":
        return 1000000000000
    if w == "tens of millions":
        return 10000000
    if w == "tens of billions":
        return 10000000000
    if w == "hundreds of millions":
        return 100000000
    if w == "hundreds of billions":
        return 100000000000
    
    print("Could not translate: " + w + " to number")
    return 1

def change_to_numeral(number, numeric_word):
    number = number.replace(",", "")
    raw_number = float(number) * word_to_number(numeric_word)
    if str(raw_number).endswith(".0"):
        raw_number = int(raw_number)
    return raw_number

def mod_amount(currency, amount, mod):
    if mod is None:
        return currency, amount, None, None
    if mod == "MIN":
        return currency, None, amount, None
    if mod == "MAX":
        return currency, None, None, amount
    if mod == "UNC":
        return currency, None, None, None

def replace_small_written_numbers(s):
    for key, value in small_numbers.items():
        s = re.sub(r"\b" + key + r"\b", value, s, re.I)
    return s

def normalize(s):
    s = whitespace_re.sub(" ", s)
    for p in irrelevant_prefixes:
        if s.startswith(p):
            s = s[len(p):]
            s = s.strip()
    for suf in irrelevant_suffixes:
        if s.endswith(suf):
            s = s[0:-len(suf)]
            s = s.strip()

    s = replace_small_written_numbers(s)

    mod = None
    s, c = minimum_mod_re.subn("", s)
    if c > 0:
        mod = "MIN"
    s, c = maximum_mod_re.subn("", s)
    if c > 0:
        mod = "MAX"
    s, c = unclear_mod_re.subn("", s)
    if c > 0:
        mod = "UNC"

    m = r1.match(s)
    if m:
        currency = lookup_currency(m.group(2))
        minimum_amount = change_to_numeral("2", m.group(1))
        return currency, None, minimum_amount, None

    m = r2.match(s)
    if m:
        currency = lookup_currency(m.group(1))
        currency_amount = change_to_numeral(m.group(2), m.group(3))
        return mod_amount(currency, currency_amount, mod)

    m = r3.match(s)
    if m:
        currency = lookup_currency(m.group(1))
        currency_amount = change_to_numeral(m.group(2), None)
        return mod_amount(currency, currency_amount, mod)

    m = r8.match(s)
    if m:
        currency = lookup_currency(m.group(2))
        currency_amount = change_to_numeral(m.group(1), None)
        return mod_amount(currency, currency_amount, mod)

    m = r9.match(s)
    if m:
        currency = lookup_currency(m.group(3))
        currency_amount = change_to_numeral(m.group(1), m.group(2))
        return mod_amount(currency, currency_amount, mod)

    m = r11.match(s)
    if m:
        currency = lookup_currency(m.group(1))
        currency_amount = change_to_numeral(m.group(2), m.group(3))
        return mod_amount(currency, currency_amount, mod)

    m = r12.match(s)
    if m:
        currency = lookup_currency(m.group(4))
        currency_amount = change_to_numeral(m.group(2), m.group(3))
        return mod_amount(currency, currency_amount, mod)
       
    m = r13.match(s)
    if m:
        currency = lookup_currency(m.group(1))
        return currency, None, None, None

    m = r14.match(s)
    if m:
        currency = lookup_currency(m.group(1))
        currency_amount = change_to_numeral("1", m.group(2))
        return mod_amount(currency, currency_amount, mod)

    m = r15.match(s)
    if m:
        currency = lookup_currency(m.group(2))
        currency_minimum = change_to_numeral(m.group(3), None)
        currency_maximum = change_to_numeral(m.group(6), None)
        return currency, None, currency_minimum, currency_maximum

    m = r16.match(s)
    if m:
        currency = lookup_currency(m.group(2))
        currency_minimum = change_to_numeral(m.group(3), m.group(4))
        currency_maximum = change_to_numeral(m.group(7), m.group(8))
        return currency, None, currency_minimum, currency_maximum

    m = r17.match(s)
    if m:
        currency = lookup_currency(m.group(3))
        minimum_amount = change_to_numeral("3", m.group(2))
        return currency, None, minimum_amount, None

    m = r18.match(s)
    if m:
        currency = lookup_currency(m.group(2))
        minimum_amount = change_to_numeral(m.group(3), m.group(7))
        maximum_amount = change_to_numeral(m.group(6), m.group(7))
        return currency, None, minimum_amount, maximum_amount

    m = r19.match(s)
    if m:
        currency = lookup_currency(m.group(5))
        minimum_amount = change_to_numeral(m.group(2), None)
        maximum_amount = change_to_numeral(m.group(4), None)
        return currency, None, minimum_amount, maximum_amount
    
    return None, None, None, None


if __name__ == "__main__":
    s = "$)"
    print(str(normalize(s)))

 
