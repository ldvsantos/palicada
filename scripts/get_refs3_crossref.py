import urllib.request
import urllib.parse
import json

q = 'plinthosols tropical weathering geochemistry'
url = f"https://api.crossref.org/works?query={urllib.parse.quote(q)}&select=DOI,title,author,issued,container-title&rows=5&sort=relevance"
req = urllib.request.Request(url, headers={'User-Agent': 'vidal-research'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for item in data['message']['items']:
            item_c = item.get('container-title')
            journal = item_c[0] if type(item_c)==list and len(item_c)>0 else item_c
            year = item.get('issued', {}).get('date-parts', [[None]])[0][0]
            authors = item.get('author', [])
            author_name = authors[0].get('family', '') if authors else 'Unknown'
            title = item.get('title',[''])[0]
            doi = item.get('DOI', '')
            print(f"{author_name} ({year}): {title} | {journal} | {doi}")
except Exception as e:
    print(f"Error: {e}")
