#!/usr/bin/env python3

import os
import re
from glob import glob
import json
import nltk
nltk.download('crubadan', quiet = True)
nltk.download('punkt', quiet = True)
nltk.download('stopwords', quiet = True)
from nltk.stem import SnowballStemmer
import pycountry
from html2text import html2text
from multiprocessing import Pool, cpu_count

from nltk.tokenize import word_tokenize
from nltk.tokenize import MWETokenizer
from nltk.corpus import stopwords

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))
all_stop_words = german_stop_words.union(english_stop_words)

from guess import *

nlp_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(os.path.dirname(nlp_dir), 'data')
results_dir = os.path.join(os.path.dirname(nlp_dir), 'results')


def multi_word_locations():
  cities = all_cities()
  locations = [w.split() for w in list(cities.keys()) + list(cities.values())]
  locations = [tuple(w) for w in locations if len(w) > 1]
  return locations

multi_word_tokenizer = MWETokenizer(multi_word_locations(), separator=' ')

def clean_text(text):
  # remove hyphens
  text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', text, flags = re.MULTILINE)

  text = remove_markdown(text)

  text = expand_words(text)

  # add space around EUR/€
  text = re.sub(r'(EUR|€)', r' \1 ', text, flags = re.MULTILINE)

  # remove hyphens, underscores and slashes
  text = re.sub(r'[\-_/]', r' ', text, flags = re.MULTILINE)

  tokens = multi_word_tokenizer.tokenize(word_tokenize(text.lower()))
  words = [clean_word(word) for word in tokens]
  words = [word for word in words if word and word not in all_stop_words]

  return words

def clean_word(word):
  if word in [':', '*', '#', ',', ';', '.', '(', ')', '&', '„', '“', '@', '?', '!', '<', '>', '’', '”', '–', '…', '•', '‘']:
    return None

  if word in ['€', 'eur', 'euro']:
    return '€'

  # remove trailing dots
  word = re.sub(r'\.$', '', word)

  # replace k suffix in numbers
  word = re.sub(r'^(\d+)k$', '\\1000', word)

  # replace ½ suffix in numbers
  word = re.sub(r'^(\d+)½$', '\\1.5', word)

  # normalise number format
  match = re.search(r'^(\d+(?:[\',.]\d{3})*)([\',.]\d\d?)?$', word)
  if match:
    int_part = re.sub(r'[\',.]', r'', match.group(1))

    if match.group(2):
      dec_part = re.sub(r'[\',.]', r'.', match.group(2))
    else:
      dec_part = ''

    return '%s%s' % (int_part, dec_part)

  return word

def map_state(word):
  states = {
    'w': 'Wien',
    's': 'Salzburg',
    't': 'Tirol',
    'st': 'Steiermark',
    'oö': 'Oberösterreich',
    'nö': 'Niederösterreich',
    'v': 'Vorarlberg',
    'k': 'Kärnten',
    'b': 'Burgenland',
  }

  return states.get(word, word)

def parse_file(path):
  with open(path) as file:
    json_data = json.load(file)

  title = html2text(json_data['title'])
  body = html2text(json_data['body'])

  words = clean_text(body)

  # print(path)
  # print(title)

  # print(words)

  data = {}

  # data['language'] = detect_language(' '.join(words))

  if json_data.get('location', None):
    data['location'] = guess_location([map_state(word) for word in clean_text(json_data['location'])])
  else:
    data['location'] = { 'cities': [], 'states': [] }

  if not data['location']['cities'] or not data['location']['states']:
    location = guess_location(words)
    data['location']['cities'] = list(set(data['location']['cities'] + location['cities']))
    data['location']['states'] = list(set(data['location']['states'] + location['states']))

  data['salary'] = guess_salary(words)
  data['degrees'] = guess_degrees(words)

  if json_data.get('contract_type', None):
    data['employment_type'] = guess_employment_types(clean_text(json_data['contract_type']))
  else:
    data['employment_type'] = []

  data['employment_type'] = list(set(data['employment_type'] + guess_employment_types(words)))
  data['experience'] = guess_experience(words)

  print(data)

  print("-" * 100)

  return data

def remove_markdown(text):
  # remove markdown images
  text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', text, flags = re.MULTILINE)

  # remove markdown links
  text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text, flags = re.MULTILINE)

  return text

def expand_words(text):
  text = re.sub(r'\bSt\.\s+Pölten\b', 'Sankt Pölten', text, flags = re.MULTILINE)
  return text

if __name__ == '__main__':
  data = glob(os.path.join(data_dir, '*.json'))

  threads = cpu_count()
  threads = 1
  pool = Pool(threads)
  result = pool.map(parse_file, data)

  os.makedirs(results_dir, exist_ok = True)
  result_path = os.path.join(results_dir, 'all.json')

  with open(result_path, 'w+') as file:
    json.dump(result, file)


  print('Total Results:', len(result))
  # print('Language found for ', sum([1 for v in result if v['language']]))
  print('Salary found for ', sum([1 for v in result if v['salary']]))
  print('Degrees found for ', sum([1 for v in result if v['degrees']]))
  print('Employment type found for ', sum([1 for v in result if v['employment_type']]))
  print('Places found for ', sum([1 for v in result if v['location']['cities'] or v['location']['states']]))
