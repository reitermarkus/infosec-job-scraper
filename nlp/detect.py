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
from html2text import HTML2Text
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

def multi_words(words):
  multi_words = [w.lower().split() for w in words]
  multi_words = [tuple(w) for w in multi_words if len(w) > 1]
  return multi_words

def multi_word_locations():
  cities = all_cities()
  return multi_words(list(cities.keys()) + list(cities.values()))

def multi_word_certifications():
  return multi_words(list(CERTIFICATIONS.keys()) + list(CERTIFICATIONS.values()))

multi_word_tokenizer = MWETokenizer(multi_word_locations() + multi_word_certifications(), separator=' ')

def clean_text(text):
  # remove hyphens
  text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', text, flags = re.MULTILINE)

  text = remove_markdown(text)

  text = expand_words(text)

  # add space around EUR/€
  text = re.sub(r'(EUR|€)', r' \1 ', text, flags = re.MULTILINE)

  text = re.sub(r'Lower\s+Austria', r'Niederösterreich', text, flags = re.MULTILINE | re.IGNORECASE)
  text = re.sub(r'Upper\s+Austria', r'Oberösterreich', text, flags = re.MULTILINE | re.IGNORECASE)
  text = re.sub(r'Vienna', r'Wien', text, flags = re.MULTILINE | re.IGNORECASE)
  text = re.sub(r'Tyrol', r'Tirol', text, flags = re.MULTILINE | re.IGNORECASE)
  text = re.sub(r'Styria', r'Steiermark', text, flags = re.MULTILINE | re.IGNORECASE)
  text = re.sub(r'Carinthia', r'Kärnten', text, flags = re.MULTILINE | re.IGNORECASE)

  # remove hyphens, underscores and slashes
  text = re.sub(r'[\-_/]', r' ', text, flags = re.MULTILINE)

  text = re.sub(r'ISO(?:.IEC)?\s*(\d+)', ' ISO/IEC \\1 ', text, flags = re.MULTILINE)

  tokens = multi_word_tokenizer.tokenize(word_tokenize(text.lower()))
  words = [clean_word(word) for word in tokens]
  words = [word for word in words if word and word not in all_stop_words]

  return words

def clean_word(word):
  if word in [':', '*', '#', ',', ';', '.', '(', ')', '&', '„', '“', '@', '?', '!', '<', '>', '’', '”', '–', '…', '•', '‘', '/', ':']:
    return None

  if word in ['€', 'eur', 'euro', 'euros']:
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

  if not is_relevant(json_data['title'].lower()):
    return None

  html2text = HTML2Text()
  html2text.ignore_emphasis = True
  html2text.ignore_links = True
  html2text.ignore_images = True
  html2text.ignore_tables = True
  title = html2text.handle(json_data['title'])
  body = html2text.handle(json_data['body'])

  words = clean_text(body)

  # print(path)
  # print(title)

  # print(words)

  data = {}

  data['language'] = detect_language(body[:512])

  if json_data.get('location', None):
    data['location'] = guess_location([map_state(word) for word in clean_text(json_data['location'])])
  else:
    data['location'] = { 'cities': [], 'states': [] }

  if not data['location']['cities'] or not data['location']['states']:
    location = guess_location(words)
    data['location']['cities'] = list(set(data['location']['cities'] + location['cities']))
    data['location']['states'] = list(set(data['location']['states'] + location['states']))

  data['salary'] = guess_salary(words)
  data['education_type'] = guess_education(words)

  if json_data.get('contract_type', None):
    data['employment_type'] = guess_employment_types(clean_text(json_data['contract_type']))
  else:
    data['employment_type'] = []

  data['employment_type'] = list(set(data['employment_type'] + guess_employment_types(words)))
  data['experience'] = guess_experience(words)

  data['certifications'] = guess_certifications(words)

  print(data)
  print("-" * 100)

  return data

def is_relevant(job_title):
  information = re.search(r'(information|\bit\b)', job_title) is not None
  cyber = re.search(r'cyber', job_title) is not None
  security = re.search(r'(sicherheit|security)', job_title) is not None
  officer = re.search(r'officer', job_title) is not None
  specialist = re.search(r'(specialist|spezialist)', job_title) is not None
  expert = re.search(r'(expert|experte)', job_title) is not None
  audit = re.search(r'audit', job_title) is not None
  evaluator = re.search(r'evaluator', job_title) is not None
  consultant = re.search(r'consultant', job_title) is not None
  tester = re.search(r'tester', job_title) is not None
  penetration = re.search(r'penetration', job_title) is not None
  network = re.search(r'(network|netzwerk)', job_title) is not None
  return (cyber and security) or (information and security) or (security and officer) or (security and specialist) or (security and expert) or (information and audit) or (security and audit) or (security and evaluator) or (security and consultant) or (security and tester) or (penetration and tester) or (network and security)

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
  # threads = 1
  pool = Pool(threads)
  result = pool.map(parse_file, data)

  os.makedirs(results_dir, exist_ok = True)
  result_path = os.path.join(results_dir, 'all.json')

  result = [r for r in result if r]

  with open(result_path, 'w+') as file:
    json.dump(result, file)

  print('Total Results:', len(result))
  # print('Language found for ', sum([1 for v in result if v['language']]))
  print('Salary found for ', sum([1 for v in result if v['salary']]))
  print('Education Type found for ', sum([1 for v in result if v['education_type']]))
  print('Employment type found for ', sum([1 for v in result if v['employment_type']]))
  print('Places found for ', sum([1 for v in result if v['location']['cities'] or v['location']['states']]))
  print('Certifications found for ', sum([1 for v in result if v['certifications']]))
