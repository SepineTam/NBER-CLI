import asyncio
import os

from flask import Flask, render_template_string, request

from ..core.download.downloader import main_download_multiple

DEFAULT_SAVE_PATH = os.path.expanduser("~/Documents/nber_paper")
app = Flask(__name__)

FORM = """
<!doctype html>
<html>
  <head>
    <title>NBER CLI Web</title>
    <style>
      body {font-family: Arial, sans-serif; margin: 2em;}
      textarea {width: 100%; height: 6em;}
      .message {color: green;}
    </style>
  </head>
  <body>
    <h1>Download NBER Papers</h1>
    <form method=post>
      <label for="paper_ids">Paper IDs (space or newline separated):</label><br>
      <textarea name="paper_ids" id="paper_ids"></textarea><br>
      <input type=submit value=Download>
    </form>
    <p class="message">{{message}}</p>
  </body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        ids_raw = request.form.get('paper_ids', '')
        paper_ids = [pid.strip() for pid in ids_raw.split() if pid.strip()]
        if paper_ids:
            asyncio.run(main_download_multiple(paper_ids, DEFAULT_SAVE_PATH))
            message = f"Downloaded {', '.join(paper_ids)}"
        else:
            message = 'Please enter at least one paper ID.'
    return render_template_string(FORM, message=message)


def run():
    app.run()
