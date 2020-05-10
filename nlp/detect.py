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

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))
all_stop_words = german_stop_words.union(english_stop_words)

from guess import *

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
    data['experience'] = guess_experience(words)

    print(data)

    print("-" * 100)

    return data

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
