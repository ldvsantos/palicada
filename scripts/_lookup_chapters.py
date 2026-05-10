import urllib.request, urllib.parse, json
queries = [
    ('Textbook of Forest Science', '10.1007/978-981-97-8289'),
    ('Agroforestry Anecdotal to Modern Science', '10.1007/978-981-10-7650'),
    ('Biotechnological Approaches for Sustaining Forest Trees', '10.1007/978-981-97-4363'),
]
for label, prefix in queries:
    print('===', label, '===')
    url = f'https://api.crossref.org/works?query.container-title={urllib.parse.quote(label)}&rows=200&select=DOI,title,author,page,container-title,type'
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=60).read())['message']['items']
    except Exception as e:
        print('ERR', e); continue
    for it in data:
        doi = it.get('DOI','')
        if not doi.startswith(prefix):
            continue
        title = (it.get('title') or [''])[0]
        ctitle = (it.get('container-title') or [''])[0]
        authors = '; '.join(f"{a.get('family','')}, {a.get('given','')}" for a in it.get('author',[]))
        print(f"  - {title} | {authors} | {doi}")
