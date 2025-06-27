import os
import asyncio
from flask import Flask, request, render_template_string
from .downloader import main_download

DEFAULT_SAVE_PATH = os.path.expanduser("~/Documents/nber_paper")
app = Flask(__name__)

FORM = """
<!doctype html>
<title>NBER CLI Web</title>
<h1>Download NBER Paper</h1>
<form method=post>
  Paper ID: <input type=text name=paper_id>
  <input type=submit value=Download>
</form>
<p>{{message}}</p>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        paper_id = request.form.get('paper_id', '').strip()
        if paper_id:
            asyncio.run(main_download(paper_id, DEFAULT_SAVE_PATH))
            message = f"Downloaded {paper_id}"
        else:
            message = 'Please enter a paper ID.'
    return render_template_string(FORM, message=message)

def run():
    app.run()
