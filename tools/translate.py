# GPL Licence
import csv
import os

translation_dictionary = dict()
with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', "translations.csv")), 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) >= 2:
            translation_dictionary[row[0]] = row[1]

def t(str_key):
    if str_key not in translation_dictionary:
        print("Warning: couldn't find translation for \"" + str_key + "\"")
        return str_key
    else:
        return translation_dictionary[str_key]