import os
import base64
from urllib.parse import urljoin, urlparse
from datetime import datetime
import subprocess
import time
import requests
from bs4 import BeautifulSoup

def download_image(img_tag, base_url):
    img_url = img_tag['src']

    if img_url.startswith("data:image"):
        data = img_url.split(",")[1]
        img_data = base64.b64decode(data)
        img_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_image.png"
        with open(img_filename, 'wb') as img_file:
            img_file.write(img_data)
    else:
        img_data = img_url.encode("utf-8")
        img_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{urlparse(img_url).path.split('/')[-1]}"
        with open(img_filename, 'wb') as img_file:
            img_file.write(img_data)

    img_tag['src'] = img_filename

def fix_relative_links(base_url, link):
    return urljoin(base_url, link)

def extract_favicon_url(soup, base_url):
    favicon_link = soup.find("link", rel="icon")
    if favicon_link:
        return urljoin(base_url, favicon_link.get("href"))
    return None

def download_favicon(favicon_url, base_url):
    if favicon_url:
        favicon_response = requests.get(favicon_url)

        if favicon_response.status_code == 200:
            favicon_data = favicon_response.content
            favicon_filename = "favicon.ico"
            with open(favicon_filename, 'wb') as favicon_file:
                favicon_file.write(favicon_data)

def delete_old_files():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    files = os.listdir(current_directory)
    for file in files:
        if file != "main.py" and file != "LICENSE" and file != "README.md" and file != "requirements.txt":
            os.remove(os.path.join(current_directory, file))

delete_old_files()

url = input("Enter the URL: ")

if not url.startswith('http://') and not url.startswith('https://'):
    url = 'https://' + url

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = response.url
    favicon_url = extract_favicon_url(soup, base_url)
    download_favicon(favicon_url, base_url)
    img_tags = soup.find_all('img', src=True)
    for img_tag in img_tags:
        download_image(img_tag, base_url)

    css_links = soup.find_all('link', rel='stylesheet')
    for link in css_links:
        css_url = urljoin(base_url, link.get('href'))
        css_response = requests.get(css_url)
        if css_response.status_code == 200:
            css_content = css_response.text
            style_tag = soup.new_tag("style")
            style_tag.string = css_content
            soup.head.append(style_tag)
            link.extract()

    links = soup.find_all('a', href=True)
    for link in links:
        link['href'] = fix_relative_links(base_url, link['href'])

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    with open(f'website_{timestamp}.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))

    print(f"Website was saved to 'website_{timestamp}.html'.")
    time.sleep(5)
    print("Closing in 5 seconds...")
else:
    print(f"Failed to copy the web page. Status code: {response.status_code}")
    time.sleep(5)
    print("Closing in 5 seconds...")
