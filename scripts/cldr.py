#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 歧視無邊，回頭是岸。鍵起鍵落，情真情幻。
dir_outcome = "data"
# Outpuing Lists
outputfn_tsv_by_locale = "CLDR_country_name_{locale}.tsv"
outinfn = "country-codes.csv"
outinfn_bak = "country-codes-backup.csv"

import os
import json

import requests
import icu  # pip install PyICU
import pandas as pd


def url_request(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r
    else:
        return None


def load_json_list(lc_file, u):
    try:
        with open(lc_file, 'r', encoding="utf-8") as infile:
            _select = json.load(infile)
            print("Loaded from local file.")
    except:
        results = url_request(url=u)
        if results is not None:
            try:
                _select = results.json()['availableLocales']['full']
                with open(lc_file, 'w', encoding="utf-8") as outfile:
                    outfile.write("{}".format(_select).replace("'", '"'))
                print("Loaded from designated url.")
            except:
                pass
    return _select


# Partial Selected Construction
# English is selected.
# Can be extended in the future: 'zh-Hant-HK', 'zh-Hant-MO',
# 'zh-Hans', 'zh-Hans-SG'
locale_select = ['en']

# Retrive data directly from unicode-cldr project hosted at github
print("Retrieve data now ...")
URL_CLDR_JSON_TERRITORIES = "https://raw.githubusercontent.com/unicode-cldr/cldr-localenames-full/master/main/{locale}/territories.json"
locale_json = {}
for l in locale_select:
    results = url_request(url=URL_CLDR_JSON_TERRITORIES.format(locale=l))
    if results is not None:
        try:
            locale_json[l] = results.json()['main'][l]['localeDisplayNames']['territories']
        except:
            pass

# Preprocessing and Generating lists
print("Preprocessing data now ...")
ITEM_NAME_CODE = "{name}[{code}]"
ITEM_CODE_NAME = "{code}:{name}"

outputlist_territories = {}
for key, value in locale_json.items():
    # Remove UN regional codes (three digits)
    value_new = {k: v for k, v in value.items() if k.isdigit() is not True}

    c_n = dict()
    for k, v in value_new.items():
        # Remove -alt-variant and -alt-short
        if len(k) > 2:
            if "-alt-variant" in k:
                print("not using:{}".format([k, v]))
                pass
            if "-alt-short" in k:  # Using -alt-short if exists
                k = k.replace("-alt-short", "")
                print("using:{}".format([k, v]))
                c_n.update({k: v})
        else:
            if k in c_n.keys():
                print ("not using:{}".format([k, v]))
            else:
                c_n.update({k: v})

    # Sort by IBM's ICU library, which uses the full Unicode Collation Algorithm
    print (key)
    collator = icu.Collator.createInstance(icu.Locale('{lc}.UTF-8'.format(lc=key)))
    c_n_keys_sorted = sorted(list(c_n.keys()))

    outputlist_territories[key] = [(x, c_n[x]) for x in c_n_keys_sorted]

df = pd.DataFrame(outputlist_territories['en'])

df.to_csv(os.path.join('data', outputfn_tsv_by_locale.format(locale='en')),
          sep='\t', encoding='utf-8', header=False, index=False)
df.columns = ['code', 'name']
df_indexed = df.set_index(['code'])

df_cc = pd.read_csv(os.path.join('data', outinfn),
                    sep=',', encoding='utf-8',
                    dtype={'ISO3166-1-numeric': 'object'},
                    keep_default_na=False, na_values=[])
df_cc_indexd = df_cc.set_index(['ISO3166-1-Alpha-2'])

# Copying the ISO names to "official_name"
df_cc_indexd['official_name_en'] = df_cc_indexd['official_name_en']

# Change the content under the coloumn "name" with CLDR names
df_cc_indexd['name'] = [df_indexed['name'].get(x, '') for x in
                        list(df_cc_indexd.index)]

df_cc_indexd = df_cc_indexd.reset_index()

columns_ordered = ['name', 'official_name_en', 'official_name_fr',
                   'ISO3166-1-Alpha-2', 'ISO3166-1-Alpha-3',
                   'ISO3166-1-numeric', 'ITU', 'MARC', 'WMO', 'DS', 'Dial',
                   'FIFA', 'FIPS', 'GAUL', 'IOC',
                   'ISO4217-currency_alphabetic_code',
                   'ISO4217-currency_country_name',
                   'ISO4217-currency_minor_unit',
                   'ISO4217-currency_name', 'ISO4217-currency_numeric_code',
                   'is_independent']

df_out = pd.DataFrame(df_cc_indexd.to_records())

df_out.to_csv(os.path.join('data', 'country-codes-cldr.csv'),
              columns=list(columns_ordered),
              sep=',', encoding='utf-8',
              index=False,
              keep_default_na=False, na_values=[])
