from flask import Flask, jsonify
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin
from rich import print
import re

app = Flask(__name__)

def get_requests(url):
    response = httpx.get(url)
    return response 

def _soup(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def scrape_product_by_ean(ean):
    url = f'https://www.bol.com/nl/nl/s/?searchtext={ean}'
    response = get_requests(url)
    soup = _soup(response)
    item_rows = soup.find_all(class_="product-item--row")
    if len(item_rows) > 0:
        title = None
        brand = None
        price = None
        seller_name = None
        seller_url = None
        item_row = item_rows[0]
        title = item_row.find(class_='product-title')
        if title:
            url = title.get('href')
            url = urljoin('https://www.bol.com',url)
            title = title.text.strip()
        brand = item_row.find(class_='product-creator')
        if brand:
            brand = brand.text.strip()
        price = item_row.find('meta', {'itemprop': 'price'}).get('content')
        seller_soup = item_row.find(class_='product-seller__link')
        if seller_soup:
            seller_name = seller_soup.text.strip()
            seller_url = seller_soup.get('href')
            seller_url = seller_url.split('?')[0]
            seller_url = urljoin('https://www.bol.com',seller_url)
        return {
            'Ean': ean,
            'Title': title,
            'Brand': brand,
            'Price': price,
            'Seller': seller_name,
            'SellerLink': seller_url,
            'Url': url,
        }   
    else:
        return None

def is_valid_ean(ean):
    ean_pattern = re.compile(r'^\d{13}$')
    return bool(ean_pattern.match(ean))
    
@app.route('/', methods=['GET'])
def home():
    return jsonify({'title': 'Bol api'})

@app.route('/ean')
def default():
    return jsonify({'error': 'Enter ean code'})

@app.route('/ean/<ean>', methods=['GET'])
def ean_details_api(ean):
    if is_valid_ean(ean):
        product_details = scrape_product_by_ean(ean)
        if product_details:
            return jsonify(product_details)
        else:
            return jsonify({'error': 'Product not found'})
    else:
        return jsonify({'error': 'Ean code is not valid.'})
        
if __name__=="__main__":
    ean = '1234567890459m'
    print(is_valid_ean(ean))
