"""Generate project pages from a publicly shared Google Drive folder."""

import datetime
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "generated-projects"
API = "https://www.googleapis.com/drive/v3/files"
START = "<!-- PROJECT LIST START -->"
END = "<!-- PROJECT LIST END -->"


def request(url, params):
    try:
        with urlopen(url + "?" + urlencode(params), timeout=60) as response:
            return response.read()
    except HTTPError as error:
        operation = "listing a folder" if url == API else "downloading a file"
        try:
            body = json.loads(error.read())
            details = body.get("error", {}).get("message", "No details provided")
        except (ValueError, AttributeError):
            details = "No details provided"
        # Do not print the request URL: it contains the API key.
        raise RuntimeError(f"Google Drive error while {operation} (HTTP {error.code}): {details}") from error


def children(folder_id, key):
    files = []
    page = None
    while True:
        params = {
            "key": key,
            "q": "'" + folder_id.replace("'", "\\'") + "' in parents and trashed = false",
            "fields": "nextPageToken,files(id,name,mimeType)",
            "pageSize": 1000,
        }
        if page:
            params["pageToken"] = page
        result = json.loads(request(API, params))
        files.extend(result.get("files", []))
        page = result.get("nextPageToken")
        if not page:
            return files


def download(file_id, key):
    return request(API + "/" + file_id, {"key": key, "alt": "media"})


def download_details(items, key):
    matches = [f for f in items if
               (f["name"].lower() == "details.txt" and f["mimeType"] == "text/plain") or
               (f["name"].lower() in ("details", "details.txt") and
                f["mimeType"] == "application/vnd.google-apps.document")]
    if len(matches) != 1:
        raise ValueError("expected exactly one details.txt text file or Google Doc named details")
    item = matches[0]
    if item["mimeType"] == "application/vnd.google-apps.document":
        if not re.fullmatch(r"[A-Za-z0-9_-]+", item["id"]):
            raise ValueError("invalid Google Doc ID")
        return request("https://docs.google.com/document/d/" + item["id"] + "/export", {"format": "txt"})
    return download(item["id"], key)


def youtube_id(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https"):
        raise ValueError("YouTube must be a valid YouTube video URL")
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        parts = parsed.path.strip("/").split("/")
        if parsed.path == "/watch":
            video = parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) == 2 and parts[0] in ("shorts", "embed", "live"):
            video = parts[1]
        else:
            video = ""
    elif host in ("youtu.be", "www.youtu.be"):
        video = parsed.path.strip("/")
    else:
        video = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video):
        raise ValueError("YouTube must be a valid YouTube video URL")
    return video


def parse_details(content):
    lines = content.decode("utf-8-sig").splitlines()
    if len(lines) < 4 or not lines[0].startswith("Title: ") or not lines[1].startswith("Date: "):
        raise ValueError("Project details must begin with 'Title: ...', 'Date: YYYY-MM', a blank line, and a description")
    title = lines[0][7:].strip()
    date = lines[1][6:].strip()
    description_start = 3
    video = None
    if lines[2].startswith("YouTube:"):
        video = youtube_id(lines[2][len("YouTube:"):].strip())
        description_start = 4
    if not title or len(lines) < description_start + 1 or lines[description_start - 1].strip():
        raise ValueError("A title and a blank line before the description are required")
    if not re.fullmatch(r"\d{4}-\d{2}", date):
        raise ValueError("Date must use YYYY-MM")
    datetime.date.fromisoformat(date + "-01")
    description = "\n".join(lines[description_start:]).strip()
    if not description:
        raise ValueError("Description cannot be empty")
    return title, date, description, video


def page(title, date, description, images, video=None):
    escape = html.escape
    photos = "\n".join(f'            <img src="{escape(name, quote=True)}">' for name in images)
    embed = ""
    if video:
        embed = f'''\n        <div class="project-video">
            <iframe src="https://www.youtube-nocookie.com/embed/{escape(video, quote=True)}" title="YouTube video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>
        </div>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} | Anthony Ozerov</title>
    <link rel="icon" type="image/png" href="../images/favicon.png">
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header class="top-bar">
        <a class="site-name" href="../index.html">Home</a>
        <nav aria-label="Main navigation">
            <a href="../projects.html">Projects</a>
            <a href="../about.html">About</a>
            <a href="../youtube.html">YouTube</a>
        </nav>
    </header>
    <main class="personal-content projects-content">
        <h1>{escape(title)}</h1>
        <p>{escape(date)}</p>
        <p class="project-description">{escape(description)}</p>
        <div class="project-photos">
{photos}
        </div>{embed}
    </main>
</body>
</html>
'''


def main():
    key = os.environ["GOOGLE_DRIVE_API_KEY"]
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    if not key or not folder_id:
        raise ValueError("Set GOOGLE_DRIVE_API_KEY and GOOGLE_DRIVE_FOLDER_ID")
    folders = [f for f in children(folder_id, key) if f["mimeType"] == "application/vnd.google-apps.folder"]
    projects = []
    outputs = {}
    for folder in folders:
        try:
            items = children(folder["id"], key)
            title, date, description, video = parse_details(download_details(items, key))
            identifier = folder["id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
                raise ValueError("invalid folder ID")
            image_names = []
            for number in (1, 2):
                candidates = [f for f in items if f["name"].lower() in (f"photo{number}.jpg", f"photo{number}.png")]
                if len(candidates) != 1:
                    raise ValueError(f"expected exactly one photo{number}.jpg or photo{number}.png")
                image = candidates[0]
                extension = image["name"].lower().rsplit(".", 1)[1]
                filename = f"{identifier}-photo{number}.{extension}"
                outputs[filename] = download(image["id"], key)
                image_names.append(filename)
            filename = identifier + ".html"
            outputs[filename] = page(title, date, description, image_names, video).encode("utf-8")
            projects.append((date, title, filename))
        except Exception as error:
            raise ValueError(f"Project folder {folder['name']!r}: {error}") from error

    projects.sort(key=lambda project: (project[0], project[1]), reverse=True)
    bars = [f'            <a class="project-bar" href="generated-projects/{html.escape(filename, quote=True)}">{html.escape(title)} - {html.escape(date)}</a>' for date, title, filename in projects]
    listing = '\n        <div class="project-list">\n' + '\n'.join(bars) + '\n        </div>\n        ' if bars else '\n        <p>No projects yet.</p>\n        '
    index_path = ROOT / "projects.html"
    index = index_path.read_text(encoding="utf-8")
    if index.count(START) != 1 or index.count(END) != 1 or index.index(START) > index.index(END):
        raise ValueError("projects.html must contain exactly one pair of project list markers")
    before, rest = index.split(START, 1)
    _, after = rest.split(END, 1)

    OUTPUT.mkdir(exist_ok=True)
    for name, data in outputs.items():
        (OUTPUT / name).write_bytes(data)
    index_path.write_text(before + START + listing + END + after, encoding="utf-8")
    print(f"Generated {len(projects)} project(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Project sync failed: {error}", file=sys.stderr)
        sys.exit(1)
