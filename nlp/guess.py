from functools import lru_cache
from itertools import tee
import json
import re
from os import path

@lru_cache(maxsize=1)
def all_cities():
  nlp_dir = path.dirname(path.realpath(__file__))

  with open(path.join(nlp_dir, 'cities.json')) as file:
    return json.load(file).items()

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

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

def guess_experience(words):
  keywords = set()

  word_count = len(words)

  for i in range(word_count):
    word = words[i]

    if re.match(r'(erfahr|kentniss|experience)', word):
      start = i - 10
      if start < 0: start = 0
      stop = i + 10
      if stop >= word_count: stop = word_count - 1
      keywords = keywords.union(set(words[start:stop]))

  return keywords
