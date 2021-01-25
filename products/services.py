import hashlib
import json
import re
import requests
from django.conf import settings

def get_products(title, active):
    url = 'http://127.0.0.1:8000/api/products/variations/' 
    params = {'title': title, 'active': active}
    r = requests.get(url, params=params)
    products = r.json()
    products_list = {'products': products['results']}
    return products_list