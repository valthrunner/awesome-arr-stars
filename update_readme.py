import re
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
ORIGINAL_REPO_README_URL = "https://raw.githubusercontent.com/Ravencentric/awesome-arr/main/README.md"
LOCAL_README_PATH = "README.md"
GITHUB_ACTIONS_BADGE = "[![Stars Update Action](https://github.com/valthrunner/awesome-arr-stars/actions/workflows/update_readme.yml/badge.svg)](https://github.com/valthrunner/awesome-arr-stars/actions/workflows/update_readme.yml)\n\n"

def fetch_latest_readme():
    try:
        response = requests.get(ORIGINAL_REPO_README_URL)
        response.raise_for_status()
        with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Fetched the latest README from the original repository.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the original README: {e}")
        if not os.path.exists(LOCAL_README_PATH):
            print("Creating an empty README.md as fallback.")
            with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
                file.write("# README\n\nThis README was created automatically.\n")
        return os.path.exists(LOCAL_README_PATH)

def format_star_count(count):
    if count >= 1000:
        formatted_count = f"{count:,}"
        return f"**{formatted_count}** 💫"
    elif count >= 200:
        formatted_count = f"{count:,}"
        return f"**{formatted_count}** 🌟"
    else:
        formatted_count = str(count)
        return f"{formatted_count} ⭐"

def clean_github_url(url):
    url = url.rstrip('/')
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)', url)
    if match:
        return f"https://github.com/{match.group(1)}/{match.group(2)}"
    else:
        return None

def get_star_count(repo_url):
    clean_url = clean_github_url(repo_url)
    if not clean_url:
        return None
    owner_repo_match = re.match(r'https://github\.com/([^/]+)/([^/]+)', clean_url)
    if not owner_repo_match:
        return None
    owner, repo = owner_repo_match.groups()
    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    try:
        response = requests.get(api_url, headers=HEADERS)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        repo_data = response.json()
        return repo_data.get('stargazers_count', 0)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching star count for {repo_url}: {e}")
        return None

def find_github_from_website(url, link_text=None):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        github_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'github.com' in href:
                clean_link = clean_github_url(href)
                if clean_link:
                    github_links.append(clean_link)
        if github_links:
            domain = urlparse(url).netloc.lower()
            for link in github_links:
                owner_repo = re.match(r'https://github\.com/([^/]+)/([^/]+)', link)
                if owner_repo:
                    owner, repo = owner_repo.groups()
                    if domain in owner.lower() or domain in repo.lower():
                        print(f"Found matching GitHub link: {link} for {url}")
                        return link
                    if link_text and (link_text.lower() in owner.lower() or link_text.lower() in repo.lower()):
                        print(f"Found matching GitHub link by link text: {link} for {url}")
                        return link
            print(f"Found GitHub link(s) on {url}: {github_links}")
            return github_links[0]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website {url}: {e}")
    return None

def update_readme_with_stars(readme_content):
    lines = readme_content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('# Awesome *Arr'):
            lines[i] = '# Awesome *Arr with ⭐s [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)'
            break
    updated_lines = []
    for line in lines:
        updated_line = line
        match = re.search(r'- \[(.*?)\]\((.*?)\)(.*)', line)
        if match:
            link_text, link_url, rest = match.groups()
            if not link_url.startswith('http'):
                updated_lines.append(line)
                continue
            star_count = None
            if "github.com" in link_url:
                star_count = get_star_count(link_url)
            else:
                github_url = find_github_from_website(link_url, link_text)
                if github_url:
                    star_count = get_star_count(github_url)
            if star_count is not None:
                updated_line = f"- [{link_text}]({link_url}) {format_star_count(star_count)}{rest}"
        updated_lines.append(updated_line)
    return GITHUB_ACTIONS_BADGE + '\n'.join(updated_lines)

def main():
    if not fetch_latest_readme():
        print("README.md could not be fetched or created. Exiting.")
        return
    with open(LOCAL_README_PATH, 'r', encoding='utf-8') as file:
        readme_content = file.read()
    updated_readme = update_readme_with_stars(readme_content)
    with open(LOCAL_README_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_readme)
    print("README.md has been updated with star counts.")

if __name__ == '__main__':
    main()
