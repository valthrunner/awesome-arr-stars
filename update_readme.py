import re
import requests
import os
from bs4 import BeautifulSoup

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

def get_star_count(repo_url):
    match = re.match(r'https://github.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        print(f"Invalid URL format: {repo_url}")
        return None
    owner, repo = match.groups()
    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    try:
        response = requests.get(api_url, headers=HEADERS)
        if response.status_code == 404:
            print(f"Repository not found: {repo_url}")
            return None
        response.raise_for_status()
        repo_data = response.json()
        return repo_data.get('stargazers_count', 0)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching star count for {repo_url}: {e}")
        return None

def find_github_from_website(url):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        content = b""
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if b"github.com" in content:
                break
        soup = BeautifulSoup(content, 'html.parser')
        github_links = [a['href'] for a in soup.find_all('a', href=True) if 'github.com' in a['href']]
        if github_links:
            print(f"Found GitHub link(s) on {url}: {github_links}")
            return github_links[0]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website {url}: {e}")
    return None

def update_readme_with_stars(readme_content, repo_urls):
    lines = readme_content.splitlines()
    
    for i, line in enumerate(lines):
        if line.startswith('# Awesome *Arr'):
            lines[i] = '# Awesome *Arr with ⭐s [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)'
            break
    
    updated_lines = []
    for line in lines:
        updated_line = line
        for repo_url in repo_urls:
            if "github.com" not in repo_url:
                github_url = find_github_from_website(repo_url)
                if github_url:
                    print(f"Found GitHub repository: {github_url} for {repo_url}")
                    repo_url = github_url
            
            match = re.search(r'- \[(.*?)\]\(' + re.escape(repo_url) + r'\)(?: \(\d+ ⭐\))?(?: - .*)?$', line)
            if match:
                link_text = match.group(1)
                star_count = get_star_count(repo_url)
                if star_count is not None:
                    description_match = re.search(r' - (.*)$', line)
                    description = f" - {description_match.group(1)}" if description_match else ""
                    updated_line = f"- [{link_text}]({repo_url}) {format_star_count(star_count)}{description}"
                    break
        updated_lines.append(updated_line)
    
    return GITHUB_ACTIONS_BADGE + '\n'.join(updated_lines)

def main():
    if not fetch_latest_readme():
        print("README.md could not be fetched or created. Exiting.")
        return
    
    with open(LOCAL_README_PATH, 'r', encoding='utf-8') as file:
        readme_content = file.read()
    
    repo_urls = re.findall(r'https://[^)]+', readme_content)
    print(f"Found {len(repo_urls)} links.")
    
    updated_readme = update_readme_with_stars(readme_content, repo_urls)
    
    with open(LOCAL_README_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_readme)
    
    print("README.md has been updated with star counts.")

if __name__ == '__main__':
    main()
