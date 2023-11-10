import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

def download_image(img_url, save_dir):
    try:
        img_response = requests.get(img_url, stream=True)

        if img_response.status_code == 200:
            total_size = int(img_response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {os.path.basename(urlparse(img_url).path)}")

            img_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(urlparse(img_url).path)}"
            img_path = os.path.join(save_dir, img_filename)

            with open(img_path, 'wb') as img_file:
                for data in img_response.iter_content(block_size):
                    progress_bar.update(len(data))
                    img_file.write(data)

            progress_bar.close()
            return img_path
        else:
            print(f"Failed to download image: {img_url}, Status code: {img_response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def fix_relative_links(base_url, link):
    return urljoin(base_url, link)

def extract_favicon_url(soup, base_url):
    favicon_link = soup.find("link", rel="icon")
    if favicon_link:
        return urljoin(base_url, favicon_link.get("href"))
    return None

def download_favicon(favicon_url, save_dir):
    try:
        if favicon_url:
            favicon_response = requests.get(favicon_url)
            if favicon_response.status_code == 200:
                favicon_data = favicon_response.content
                favicon_filename = "favicon.ico"
                favicon_path = os.path.join(save_dir, favicon_filename)
                with open(favicon_path, 'wb') as favicon_file:
                    favicon_file.write(favicon_data)
    except Exception as e:
        print(f"Error downloading favicon: {e}")

def delete_old_files(save_dir):
    try:
        for file in os.listdir(save_dir):
            file_path = os.path.join(save_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error deleting old files: {e}")

def save_html(soup, save_dir):
    try:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = os.path.join(save_dir, f'website_{timestamp}.html')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        print(f"Website was saved to '{output_file}'.")
    except Exception as e:
        print(f"Error saving HTML: {e}")

def main():
    save_dir = 'saved'

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    delete_old_files(save_dir)

    url = input("Enter the URL: ")

    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    try:
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = response.url

            favicon_url = extract_favicon_url(soup, base_url)
            download_favicon(favicon_url, save_dir)

            img_tags = soup.find_all('img', src=True)
            for img_tag in img_tags:
                img_url = urljoin(base_url, img_tag['src'])
                img_path = download_image(img_url, save_dir)
                if img_path:
                    img_tag['src'] = os.path.basename(img_path)

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

            save_html(soup, save_dir)

        else:
            print(f"Failed to copy the web page. Status code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")

    print("Download complete. Closing in 5 seconds...")
    time.sleep(5)

if __name__ == "__main__":
    main()
