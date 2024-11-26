import re
import requests
import os
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
ORIGINAL_REPO_README_URL = "https://raw.githubusercontent.com/Ravencentric/awesome-arr/main/README.md"
LOCAL_README_PATH = "README.md"
GITHUB_ACTIONS_BADGE = "[![Stars Update Action](https://github.com/valthrunner/awesome-arr-stars/actions/workflows/update_readme.yml/badge.svg)](https://github.com/valthrunner/awesome-arr-stars/actions/workflows/update_readme.yml)\n\n"

BADGE_PATTERN = re.escape(GITHUB_ACTIONS_BADGE.strip())

def fetch_latest_readme():
    print("Fetching the latest README from the original repository...")
    try:
        response = requests.get(ORIGINAL_REPO_README_URL)
        response.raise_for_status()
        with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Successfully fetched and saved the latest README.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error fetching README: {e}")
        if not os.path.exists(LOCAL_README_PATH):
            print("Local README does not exist. Creating a default README.")
            with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
                file.write("# README\n\nThis README was created automatically.\n")
        else:
            print("Using the existing local README.")
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
    match = re.match(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
    if not match:
        print(f"URL does not match repository pattern: {repo_url}")
        return None
    owner, repo = match.groups()
    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    print(f"Fetching star count for repository: {owner}/{repo}")
    try:
        response = requests.get(api_url, headers=HEADERS)
        if response.status_code == 404:
            print(f"Repository not found: {repo_url}")
            return None
        response.raise_for_status()
        repo_data = response.json()
        star_count = repo_data.get('stargazers_count', 0)
        print(f"Repository {owner}/{repo} has {star_count} stars.")
        return star_count
    except requests.exceptions.RequestException as e:
        print(f"Error fetching star count for {repo_url}: {e}")
        return None

def find_github_from_website(url):
    print(f"Searching for GitHub repository link on website: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        github_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            repo_match = re.match(r'https://github\.com/([^/]+)/([^/]+?)/?$', href)
            if repo_match:
                github_links.append(href.rstrip('/'))
        if github_links:
            print(f"Found GitHub repository link: {github_links[0]}")
            return github_links[0]
        else:
            print(f"No valid GitHub repository link found on {url}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error accessing website {url}: {e}")
        return None

def update_readme_with_stars(readme_content, repo_urls):
    print("Updating README with star counts...")
    lines = readme_content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('# Awesome *Arr'):
            print("Updating the main header of the README.")
            lines[i] = '# Awesome *Arr with ⭐s [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)'
            break
    updated_lines = []
    processed_repos = set()
    for line_number, line in enumerate(lines, start=1):
        updated_line = line
        for repo_url in repo_urls:
            if repo_url in processed_repos:
                continue
            original_repo_url = repo_url
            if "github.com" not in repo_url:
                github_url = find_github_from_website(repo_url)
                if github_url:
                    repo_url = github_url
                else:
                    print(f"Skipping URL as no GitHub repository was found: {original_repo_url}")
                    continue
            if not re.match(r'https://github\.com/[^/]+/[^/]+/?$', repo_url):
                print(f"Skipping non-repository GitHub URL: {repo_url}")
                continue
            match = re.search(r'- \[(.*?)\]\(' + re.escape(repo_url) + r'\)(?: \(\d+ ⭐(?:\w)?)?(?: - .*)?$', line)
            if match:
                link_text = match.group(1)
                print(f"Processing repository: {repo_url}")
                star_count = get_star_count(repo_url)
                if star_count is not None:
                    description_match = re.search(r' - (.*)$', line)
                    description = f" - {description_match.group(1)}" if description_match else ""
                    updated_line = f"- [{link_text}]({repo_url}) {format_star_count(star_count)}{description}"
                    print(f"Updated line {line_number}: {updated_line}")
                    processed_repos.add(repo_url)
                    break
        updated_lines.append(updated_line)
    # Check if badge is already present
    if not re.search(BADGE_PATTERN, '\n'.join(updated_lines)):
        print("Adding GitHub Actions badge to README.")
        updated_readme = GITHUB_ACTIONS_BADGE + '\n'.join(updated_lines)
    else:
        print("GitHub Actions badge already present. Skipping addition.")
        updated_readme = '\n'.join(updated_lines)
    print("Finished updating star counts in README.")
    return updated_readme

def main():
    print("Starting README update process...")
    if not fetch_latest_readme():
        print("Failed to fetch or create the README file.")
        return
    with open(LOCAL_README_PATH, 'r', encoding='utf-8') as file:
        readme_content = file.read()
    repo_urls = set(re.findall(r'https://[^\s)]+', readme_content))
    # Exclude badge URLs
    badge_urls = set(re.findall(r'https://[^\s)]+', GITHUB_ACTIONS_BADGE))
    repo_urls -= badge_urls
    print(f"Found {len(repo_urls)} unique URLs in the README after excluding badge URLs.")
    updated_readme = update_readme_with_stars(readme_content, repo_urls)
    with open(LOCAL_README_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_readme)
    print("README has been updated successfully.")

if __name__ == '__main__':
    main()
