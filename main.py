import os
from dataclasses import dataclass
from datetime import datetime
from random import choice

import openai
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

CACHE_LIFETIME = int(os.getenv('CACHE_LIFETIME'))
MAX_PAGES_PER_DAY = int(os.getenv('MAX_PAGES_PER_DAY'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f'{CACHE_LIFETIME=}')
print(f'{MAX_PAGES_PER_DAY=}')
print(f'{MAX_TOKENS=}')
print(f'OPENAI_API_KEY={OPENAI_API_KEY[:3]}...{OPENAI_API_KEY[-4:]}')

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

pages_generated = 0
pages_generated_last_reset = datetime.now()


@dataclass
class CachedPage:
    path: str
    html: str
    generated_on: datetime


cache: dict[str, CachedPage] = {}


@app.route('/cached')
def route_cached():
    links = ''
    for page in cache.values():
        links += f'<li><a href="{page.path}">{page.path}</a> (Generated on {page.generated_on})<br></li>'

    return f'<html>' \
           f'<head>' \
           f'  <title>Cached pages</title>' \
           f'</head>' \
           f'<body>' \
           f'  <h1>Cached AI-generated pages:</h1>' \
           f'  <ul>' \
           f'    {links}' \
           f'  </ul>' \
           f'</body>' \
           f'</html>'


@app.route('/')
def route_root():
    placeholders = ['information-about-unicorns', 'javascript-projects/pong-game', 'how-to-brew-beer',
                    'how-to-develop-an-ai', 'javascript-projects/monte-carlo-simulation-to-calculate-pi',
                    'news-articles', 'page-list', 'hello-world', 'my-projects']

    return f'<html>' \
           f'<head>' \
           f'  <title>The everything website</title>' \
           f'</head>' \
           f'<body>' \
           f'  <h2>AI-generated pages.</h2>' \
           f'  <p>' \
           f'  Every page on this website except this one and <a href="/cached">the list of cached pages</a> are AI-generated.<br>' \
           f'  Because AI is slow, loading a page for the first time can take a few seconds.<br>' \
           f'  Feel free to enter any URL or topic you\'d like, or use this input section below:<br>' \
           f'  <input type="text" id="url" placeholder="{choice(placeholders)}">' \
           f'  <button onclick="location.href=document.getElementById(\'url\').value.replaceAll(\' \', \'-\')">Go</button><br>' \
           f'  </p>' \
           f'</body>' \
           f'</html>'


@app.route('/<path:url>')
def route_path(url=''):
    global pages_generated, pages_generated_last_reset
    if (datetime.now() - pages_generated_last_reset).total_seconds() > 86400:  # 1 day
        pages_generated = 0
        pages_generated_last_reset = datetime.now()
        print('Reset pages_generated.')

    path = f'/{url}'
    if path == '/favicon.ico':
        return 'no', 404

    if path in cache:
        page = cache[path]
        if pages_generated < MAX_PAGES_PER_DAY and (datetime.now() - page.generated_on).total_seconds() > CACHE_LIFETIME:
            del cache[path]
        else:
            html = page.html.replace('<title>', '<title>[CACHED] ')
            return html

    if pages_generated >= MAX_PAGES_PER_DAY:
        return 'Maximum number of generated pages reached. In the meanwhile, check out the <a href="/cached">cached pages</a>.'

    pages_generated += 1
    html = generate_html(path)

    cache[path] = CachedPage(
        path=path,
        html=html,
        generated_on=datetime.now(),
    )

    return html


def generate_html(path) -> str:
    html = complete(f'The following is the HTML for a website. Note the following:\n'
                    f'- The page is dynamically generated each time the page is loaded.\n'
                    f'- The content is based on the path.\n'
                    f'- The page contains interesting stuff for the user to interact with, eg. links to explore more dynamically generated pages.\n'
                    f'- The page has a title.\n'
                    f'- The page does not need external files, eg. JavaScript, CSS or images.\n'
                    f'\n'
                    f'The path is {path}:\n')

    html = html.strip()
    if html.startswith('```'):
        html = html[3:]
    if html.endswith('```'):
        html = html[:-3]

    return html


def complete(prompt) -> str:
    res = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=0.7
    )

    return res['choices'][0]['text']


if __name__ == '__main__':
    print('Hello, world.')
    app.run(host='0.0.0.0', port=8080, debug=False)
