import re
import requests
import os

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

ORIGINAL_REPO_README_URL = "https://raw.githubusercontent.com/Ravencentric/awesome-arr/main/README.md"
LOCAL_README_PATH = "README.md"

def fetch_readme(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_github_links(readme_content):
    pattern = r'\[.*?\]\((https://github\.com/[\w\-/]+)\)'
    return re.findall(pattern, readme_content)

def get_star_count(repo_url):
    repo_path = repo_url.replace("https://github.com/", "")
    api_url = f"https://api.github.com/repos/{repo_path}"
    try:
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("stargazers_count", 0)
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"Repository not found for {repo_url}. Skipping...")
            return None
        else:
            raise e  

def update_readme_with_stars(readme_content, links):
    updated_content = readme_content
    for link in links:
        star_count = get_star_count(link)
        if star_count is not None:

            pattern = r'(\[.*?\]\({}\))'.format(re.escape(link))
            replacement = r"\1 {} ⭐".format(star_count)
            updated_content = re.sub(pattern, replacement, updated_content)
    return updated_content

def main():

    readme_content = fetch_readme(ORIGINAL_REPO_README_URL)

    github_links = extract_github_links(readme_content)
    print(f"Found {len(github_links)} GitHub links.")

    updated_readme = update_readme_with_stars(readme_content, github_links)

    with open(LOCAL_README_PATH, "w", encoding="utf-8") as file:
        file.write(updated_readme)
    print("README.md updated with star counts.")

if __name__ == "__main__":
    main()
