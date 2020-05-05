#!/usr/bin/env python3

from os import path
import re
from glob import glob
import json
import nltk
nltk.download('crubadan', quiet = True)
nltk.download('punkt', quiet = True)
from nltk.stem import SnowballStemmer
import pycountry
from html2text import html2text
from multiprocessing import Pool, cpu_count

from nltk.tokenize import word_tokenize

from itertools import tee

def detect_language(text):
  tc = nltk.classify.textcat.TextCat()
  guess = tc.guess_language(text)
  return pycountry.languages.get(alpha_3 = guess).alpha_2

def guess_degrees(words):
  degrees = set()

  for word in words:
    if not isinstance(word, str):
      continue

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
  salaries = []

  for (w1, w2) in pairwise(words):
    if w1 == '€' and isinstance(w2, float):
      salaries += [w2]

    if w2 == '€' and isinstance(w1, float):
      salaries += [w1]

  return salaries

def guess_employment_types(words):
  types = set()

  for word in words:
    if not isinstance(word, str):
      continue

    if re.match(r'(vollzeit|full(-|\s*)time)', word):
      types.add('full-time')

    if re.match(r'(teilzeit|part(-|\s*)time)', word):
      types.add('part-time')

  for (hours, word) in pairwise(words):
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
  words = [word for word in words if word]

  return words

def clean_word(word):
  if word in [':', '*', '#', ',', ';', '.', '(', ')', '&', '„', '“', '@', '?', '!', '<', '>', '’', '”', '–']:
    return None

  if word in ['€', 'eur', 'euro']:
    return '€'

  match = re.search(r'^\d+(\.\d{3})*(,\d\d?)?$', word)
  if match:
    number = re.sub(r'\.', r' ', word)
    number = re.sub(r',', r'.', number)
    number = re.sub(r' ', r'', number)
    return float(number)

  match = re.search(r'^\d+(,\d{3})*(\.\d\d?)?$', word)
  if match:
    number = re.sub(r',', r'', word)
    return float(number)

  return word

def parse_file(path):
  with open(path) as file:
    json_data = json.load(file)

    title = html2text(json_data['title'])
    body = html2text(json_data['body'])

    words = clean_text(body)

    # language = detect_language(cleaned_body)

    print(path)
    print(title)

    print(words)

    salary = guess_salary(words)
    print("salary", salary)
    json_data['salary'] = salary

    degrees = guess_degrees(words)
    print("degrees", degrees)
    json_data['degrees'] = degrees

    employment_types = guess_employment_types(words)
    print("employment_type", employment_types)
    json_data['employment_type'] = employment_types

    # print(language)

    print("-" * 100)

    return json_data

if __name__ == '__main__':
  data_dir = path.join(path.dirname(path.dirname(path.realpath(__file__))), 'data')
  data = glob(path.join(data_dir, '*.json'))

  threads = cpu_count()
  threads = 1
  pool = Pool(threads)
  result = pool.map(parse_file, data)

  print('Total Results:', len(result))
  print('Salary found for ', sum([1 for v in result if v['salary']]))
  print('Degrees found for ', sum([1 for v in result if v['degrees']]))
  print('Employment type found for ', sum([1 for v in result if v['employment_type']]))
