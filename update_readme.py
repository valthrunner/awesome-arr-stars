import re
import requests
import os

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
ORIGINAL_REPO_README_URL = "https://raw.githubusercontent.com/Ravencentric/awesome-arr/main/README.md"
LOCAL_README_PATH = "README.md"

def fetch_latest_readme():
    try:
        response = requests.get(ORIGINAL_REPO_README_URL)
        response.raise_for_status()
        with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Fetched the latest README from the original repository.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the original README: {e}")
        if not os.path.exists(LOCAL_README_PATH):
            print("Creating an empty README.md as fallback.")
            with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
                file.write("# README\n\nThis README was created automatically.\n")

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

def update_readme_with_stars(readme_content, repo_urls):
    updated_lines = []
    for line in readme_content.splitlines():
        match = re.search(r'\((https://github.com/[^)]+)\)', line)
        if match:
            repo_url = match.group(1)
            if repo_url in repo_urls:
                star_count = get_star_count(repo_url)
                if star_count is not None:
                    line = re.sub(r'\(\d+ ⭐\)', f'({star_count} ⭐)', line)
        updated_lines.append(line)
    return '\n'.join(updated_lines)

def main():
    fetch_latest_readme()
    with open(LOCAL_README_PATH, 'r', encoding='utf-8') as file:
        readme_content = file.read()

    repo_urls = re.findall(r'https://github.com/[^)]+', readme_content)
    print(f"Found {len(repo_urls)} GitHub links.")

    updated_readme = update_readme_with_stars(readme_content, repo_urls)

    with open(LOCAL_README_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_readme)
    print("README.md has been updated with star counts.")

if __name__ == '__main__':
    main()
