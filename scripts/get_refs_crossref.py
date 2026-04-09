import urllib.request
import urllib.parse
import json

queries = [
    "gully erosion susceptibility tropical soils",
    "piping erosion gully development soils",
]

for q in queries:
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(q)}&select=DOI,title,author,issued,container-title&rows=3&sort=relevance"
    req = urllib.request.Request(url, headers={'User-Agent': 'vidal-research'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"--- Query: {q} ---")
            for item in data['message']['items']:
                title = item.get('title',[''])[0]
                authors = item.get('author', [])
                author_name = authors[0].get('family', '') if authors else 'Unknown'
                year = item.get('issued', {}).get('date-parts', [[None]])[0][0]
                journal = item.get('container-title',[''])[0] if type(item.get('container-title'))==list else item.get('container-title','')
                doi = item.get('DOI', '')
                print(f"Title: {title}")
                print(f"Author: {author_name}")
                print(f"Year: {year}")
                print(f"Journal: {journal}")
                print(f"DOI: {doi}")
                print()
    except Exception as e:
        print(f"Error: {e}")
