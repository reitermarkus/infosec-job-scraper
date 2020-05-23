import nltk
import pycountry
from functools import lru_cache
from itertools import tee
import json
import re
from os import path

@lru_cache(maxsize=1)
def all_cities():
  nlp_dir = path.dirname(path.realpath(__file__))

  with open(path.join(nlp_dir, 'cities.json')) as file:
    return json.load(file)

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def map_number(word):
  return float(word) if re.match(r'^\d+(\.\d\d?)?$', word) is not None else word

def detect_language(text):
  tc = nltk.classify.textcat.TextCat()
  guess = tc.guess_language(text).strip()
  return pycountry.languages.get(alpha_3 = guess).alpha_2


CERTIFICATIONS = {
  'CEH': 'Certified Ethical Hacker',
  'CISA': 'Certified Information Security Auditor',
  'CISM': 'Certified Information Security Manager',
  'CISSP': 'Certified Information Systems Security Professional',
  'CRISC': 'Certified in Risk and Information Systems Control',
  'ITIL': 'Information Technology Infrastructure Library',
  'CIA': 'Certified Internal Auditor',
  'ISO/IEC 27001': 'Information Technology Security Techniques',
  'HITRUST': 'HITRUST Compliance Certification',
  'COBIT': 'COBIT Certification',
  'ISO/IEC 22301': 'Business Continuity Management',
  'CGEIT': 'Certified in the Governance of Enterprise IT',
  'GIAC': 'GIAC Cybersecurity Certification'
}

CERTIFICATIONS_LOWER = [w.lower() for w in CERTIFICATIONS.keys()]

def guess_certifications(words):
  certifications = set()

  for w in words:
    if w in CERTIFICATIONS_LOWER:
      certifications.add(w)

  return list(certifications)

def guess_location(words):
  cities = set()
  states = set()

  for city, state in all_cities().items():
    if city.lower() in words:
      cities.add(city)
      states.add(state)

    if state.lower() in words:
      states.add(state)

  return {
    'cities': list(cities),
    'states': list(states),
  }

def guess_education(words):
  degrees = set()

  for word in words:
    if re.search(r'lehre', word):
      degrees.add('Lehre')

    if re.search(r'ausbildung', word):
      degrees.add('Ausbildung')

    if re.match(r'pflichtschul', word):
      degrees.add('Pflichtschule')

    if word == 'fh' or re.search(r'hochschul', word):
      degrees.add('Bachelor')

    if word in ['htl', 'hak', 'hbla', 'hlw', 'lfs'] or re.match(r'(matura|fachschul)', word):
      degrees.add('Matura')

    if re.match(r'bachelor', word) or word in ['studium', 'university', 'universität']:
      degrees.add('Bachelor')

    if re.match(r'master', word):
      degrees.add('Master')

  return list(degrees)

def guess_salary(words):
  salaries = set()

  for (w1, w2) in pairwise([map_number(word) for word in words]):
    if w1 == '€' and isinstance(w2, float):
      salaries.add(w2)

    if w2 == '€' and isinstance(w1, float):
      salaries.add(w1)

  return list(salaries)

def guess_employment_types(words):
  types = set()

  text = ' '.join(words)

  if re.match(r'(vollzeit|full(-|\s*)time)', text):
    types.add('full-time')

  if re.match(r'(teilzeit|part(-|\s*)time)', text):
    types.add('part-time')

  if re.match(r'(feste?\s*anstellung|unbefristet)', text):
    types.add('permanent')

  if re.match(r'(?<!un)befristet', text):
    types.add('temporary')

  if re.match(r'temporäre?\s*anstellung', text):
    types.add('temporary')

  for (hours, word) in pairwise([map_number(word) for word in words]):
    if isinstance(hours, float) and word in ['wochenstunden', 'hours']:
      if hours > 20:
        types.add('full-time')
      else:
        types.add('part-time')

  return list(types)

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

  return list(keywords)
