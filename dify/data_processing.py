
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import time

API_KEY = "854555b9cd0233a148b6d9371d8975057a7d11308d4e6bed9ef3aa4a0b1d4327"
INPUT_HTML = "deepseek.html"
OUTPUT_HTML = "deepseek_new.html"

def read_html(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"读取HTML文件失败: {e}")
        return None

def write_html(filepath, content):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"新HTML已保存至: {filepath}")
    except Exception as e:
        print(f"写入HTML文件失败: {e}")

def extract_img_themes(soup):
    img_tags = soup.find_all('img')
    img_themes = [img.get('alt', '') for img in img_tags]
    return img_tags, img_themes

def search_image_url(query, api_key=API_KEY):
    params = {
        "engine": "google_images_light",
        "q": query,
        "api_key": api_key
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        images_results = results.get("images_results", [])
        if images_results and isinstance(images_results, list):
            return images_results[0].get('thumbnail')
    except Exception as e:
        print(f"搜索 '{query}' 时出错: {e}")
    return None

def main():
    html = read_html(INPUT_HTML)
    if html is None:
        return

    soup = BeautifulSoup(html, 'html.parser')
    img_tags, img_themes = extract_img_themes(soup)

    print(f"共发现 {len(img_themes)} 个图片主题。")
    result = []
    for idx, theme in enumerate(img_themes):
        print(f"[{idx+1}/{len(img_themes)}] 搜索：{theme}")
        img_url = search_image_url(theme)
        if img_url:
            print(f"  获取图片URL：{img_url}")
            result.append(img_url)
        else:
            print("  未获取到图片，保留原src。")
            result.append(img_tags[idx].get('src', ''))

        # 可选：防止API速率限制
        # time.sleep(1)

    if len(result) != len(img_tags):
        print("警告：图片数量与主题数量不一致，可能有部分图片未被替换。")

    # 替换src
    for img, new_src in zip(img_tags, result):
        img['src'] = new_src

    write_html(OUTPUT_HTML, str(soup))
    print("全部图片替换完成。")

if __name__ == "__main__":
    main()