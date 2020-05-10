#!/usr/bin/env python3

from os import path
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
from functools import lru_cache

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from itertools import tee

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))
all_stop_words = german_stop_words.union(english_stop_words)

def map_number(word):
  return float(word) if re.match(r'^\d+(\.\d\d?)?$', word) is not None else word

def detect_language(text):
  tc = nltk.classify.textcat.TextCat()
  guess = tc.guess_language(text)
  return pycountry.languages.get(alpha_3 = guess).alpha_2

def guess_places(words):
  cities = set()
  states = set()

  combined_text = ' '.join([word for word in words])

  for city, state in all_cities():
    if city in combined_text:
      cities.add(city)

    if state in combined_text:
      states.add(state)

  if cities or states:
    return {
      'cities': cities,
      'states': states,
    }

  return {}

def guess_degrees(words):
  degrees = set()

  for word in words:
    if re.match(r'lehre', word):
      degrees.add('lehre')

    if re.match(r'pflichtschul', word):
      degrees.add('pflichtschul')

    if word == 'fh' or re.match(r'fachhochschul', word):
      degrees.add('fh')

    if word in ['htl', 'hak', 'hbla', 'hlw', 'lfs'] or re.match(r'(matura|fachschul)', word):
      degrees.add('matura')

    if re.match(r'bachelor', word):
      degrees.add('bachelor')

    if re.match(r'master', word):
      degrees.add('master')

  return degrees

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def guess_salary(words):
  salaries = set()

  for (w1, w2) in pairwise([map_number(word) for word in words]):
    if w1 == '€' and isinstance(w2, float):
      salaries.add(w2)

    if w2 == '€' and isinstance(w1, float):
      salaries.add(w1)

  return salaries

def guess_employment_types(words):
  types = set()

  for word in words:
    if re.match(r'(vollzeit|full(-|\s*)time)', word):
      types.add('full-time')

    if re.match(r'(teilzeit|part(-|\s*)time)', word):
      types.add('part-time')

  for (hours, word) in pairwise([map_number(word) for word in words]):
    if isinstance(hours, float) and word in ['wochenstunden', 'hours']:
      if hours > 20:
        types.add('full-time')
      else:
        types.add('part-time')

  return types

def clean_text(text):
  # remove hyphens
  text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', text, flags = re.MULTILINE)

  # remove markdown images
  text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', text, flags = re.MULTILINE)

  # remove markdown links
  text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text, flags = re.MULTILINE)

  # add space around EUR/€
  text = re.sub(r'(EUR|€)', r' \1 ', text, flags = re.MULTILINE)

  # remove hyphens, underscores and slashes
  text = re.sub(r'[\-_/]', r' ', text, flags = re.MULTILINE)

  tokens = word_tokenize(text.lower())
  words = [clean_word(word) for word in tokens]
  words = [word for word in words if word and word not in all_stop_words]

  return words

def clean_word(word):
  if word in [':', '*', '#', ',', ';', '.', '(', ')', '&', '„', '“', '@', '?', '!', '<', '>', '’', '”', '–']:
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

def parse_file(path):
  with open(path) as file:
    json_data = json.load(file)

    title = html2text(json_data['title'])
    body = html2text(json_data['body'])

    words = clean_text(body)

    print(path)
    print(title)

    print(words)

    data = {}

    # data['language'] = detect_language(cleaned_body)
    data['salary'] = guess_salary(words)
    data['degrees'] = guess_degrees(words)
    data['employment_type'] = guess_employment_types(words)
    data['places'] = guess_places(words)

    print(data)

    print("-" * 100)

    return data

@lru_cache(maxsize=1)
def all_cities():
  nlp_dir = path.dirname(path.realpath(__file__))

  with open(path.join(nlp_dir, 'cities.json')) as file:
    return json.load(file).items()

if __name__ == '__main__':
  nlp_dir = path.dirname(path.realpath(__file__))
  data_dir = path.join(path.dirname(nlp_dir), 'data')
  data = glob(path.join(data_dir, '*.json'))

  threads = cpu_count()
  threads = 1
  pool = Pool(threads)
  result = pool.map(parse_file, data)

  print('Total Results:', len(result))
  print('Salary found for ', sum([1 for v in result if v['salary']]))
  print('Degrees found for ', sum([1 for v in result if v['degrees']]))
  print('Employment type found for ', sum([1 for v in result if v['employment_type']]))
  print('Places found for ', sum([1 for v in result if v['places']]))
