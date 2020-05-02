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

def detect_language(text):
  tc = nltk.classify.textcat.TextCat()
  guess = tc.guess_language(text)
  return pycountry.languages.get(alpha_3 = guess).alpha_2

def guess_degree(text):
  degrees = ['HTL', 'FH', 'Universität', 'Master', 'Bachelor', 'Hochschul', 'Pflichtschul', 'Mature', 'Fachschul', 'Fachhochschul', 'HAK', 'HBLA', 'HLW', 'LFS', 'Lehre']

def guess_salary(text):
  matches = re.findall(r'\s*(?:Euro|EUR|€)\s*(\d+)(?:[,.])?(\d\d\d)(?:[,.](?:-|\d\d))?', text)
  matches += re.findall(r'\s*(\d+)(?:[,.])(\d\d\d)(?:[,.](?:-|\d\d))?(?:\s*)(?:Euro|EUR|€)', text)

  if matches:
    return max(map(lambda m: float(m[0] + m[1]), matches))

  return None

def guess_employment_types(text):
  types = set()

  if re.search(r'(vollzeit|full(-|\s*)time)', text, flags = re.MULTILINE | re.IGNORECASE):
    types.add('full-time')

  if re.search(r'(teilzeit|part(-|\s*)time)', text, flags = re.MULTILINE | re.IGNORECASE):
    types.add('part-time')

  hours = re.search(r'(\d+(?:[,.]\d+)?)\s+(?:wochenstunden|hours\s*per\s*week)', text, flags = re.MULTILINE | re.IGNORECASE)

  if hours is not None:
    hours = float(re.sub(',', '.', hours.group(1)))

    if hours > 20:
      types.add('full-time')
    else:
      types.add('part-time')

  return types

def clean_text(line):
  # remove markdown formatting
  line = re.sub(r'\*\*', r' ', line, flags = re.MULTILINE)

  # remove headings and lists
  line = re.sub(r'^[\*\#\ ]*(.*)[\*\#\ ]*$', r'\1', line, flags = re.MULTILINE)

  # remove markdown images
  line = re.sub(r'!\[[^\]]*\]\([^\)]*\)', r' ', line, flags = re.MULTILINE)

  # remove markdown links
  line = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', line, flags = re.MULTILINE)

  # add space around EUR/€
  line = re.sub(r'(EUR|€)', r' \1 ', line, flags = re.MULTILINE)

  # remove trailing comma from digits
  line = re.sub(r'(\d),-', r'\1 ', line, flags = re.MULTILINE)

  # remove redundant spaces
  line = re.sub(r'\ +', r' ', line, flags = re.MULTILINE)

  return line

def parse_file(path):
  with open(path) as file:
    json_data = json.load(file)

    title = html2text(json_data['title'])
    body = html2text(json_data['body'])

    cleaned_body = clean_text(body)

    # language = detect_language(cleaned_body)

    print(path)
    print(title)
    print(cleaned_body)

    salary = guess_salary(cleaned_body)
    print("salary", salary)
    json_data['salary'] = salary

    employment_types = guess_employment_types(cleaned_body)
    print("employment_types", employment_types)
    json_data['employment_types'] = employment_types

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

  print(len(result))
  print(sum([1 for v in result if v['salary'] is not None]))
