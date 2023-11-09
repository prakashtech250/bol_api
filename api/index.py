from flask import Flask, jsonify
from bs4 import BeautifulSoup
import httpx
import asyncio
from urllib.parse import urljoin
from rich import print
import re
import time

app = Flask(__name__)
client = httpx.AsyncClient()

def get_requests(url):
    response = httpx.get(url)
    return response 

def _soup(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_rating(rating_string):
    rating_start_index = rating_string.find(":") + 1
    rating_end_index = rating_string.find("van") - 1
    rating = float(rating_string[rating_start_index:rating_end_index].replace(",", "."))
    return rating

def products_from_div(soup):
    results = []
    item_rows = soup.find_all(class_="product-item--row")
    if len(item_rows) > 0:
        for item_row in item_rows:
            productId = None
            title = None
            brand = None
            price = None
            seller_name = None
            seller_url = None
            reviews = 0
            rating = 0
            productId = item_row.get('data-id')
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
            star_rating = item_row.find(class_='star-rating')
            if star_rating:
                reviews = int(star_rating.get('data-count'))
                rating_text = star_rating.get('title')
                rating = get_rating(rating_text)
            if seller_soup:
                seller_name = seller_soup.text.strip()
                seller_url = seller_soup.get('href')
                seller_url = seller_url.split('?')[0]
                seller_url = urljoin('https://www.bol.com',seller_url)
            result = {
                'ProductId': productId,
                'Title': title,
                'Brand': brand,
                'Price': float(price),
                'Seller': seller_name,
                'SellerLink': seller_url,
                'Reviews': reviews,
                'Rating': rating, 
                'Url': url,
            } 
            results.append(result) 
    return results

def scrape_product_by_ean(ean):
    url = f'https://www.bol.com/nl/nl/s/?searchtext={ean}'
    response = get_requests(url)
    soup = _soup(response)
    product_details = products_from_div(soup)
    return product_details

def is_valid_ean(ean):
    ean_pattern = re.compile(r'^\d{13}$')
    return bool(ean_pattern.match(ean))

def store_products(storeUrl):
    response = get_requests(storeUrl)
    soup = _soup(response)
    product_details = products_from_div(soup)
    print(product_details)
    
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
    start = time.perf_counter()
    storeUrl = 'https://www.bol.com/nl/nl/w/alle-artikelen-rvcommerces/1747804/'
    store_products(storeUrl)
    end = time.perf_counter()
    print(end-start)