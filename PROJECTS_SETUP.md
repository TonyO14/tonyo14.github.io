# Project sync setup

The workflow runs on pushes to `main` and can also be run manually from GitHub's Actions tab. It generates the site and deploys it directly to GitHub Pages; generated files are not committed to the repository. Local changes must be committed and pushed before they can be published.

## Google Drive

1. Create a folder for your projects. Under Share, set General access to **Anyone with the link**, Viewer. Everything in this folder will be published, so don't put private information in it.
2. Copy the folder ID from its URL: `https://drive.google.com/drive/folders/FOLDER_ID`.
3. Create a separate subfolder inside it for each project. In each project folder, add exactly these three files:
   - A Google Doc named `details`, or an uploaded `details.txt` text file (UTF-8 encoded). Use only one per project.
   - `photo1.jpg` or `photo1.png`
   - `photo2.jpg` or `photo2.png`

Example content for the `details` Google Doc or `details.txt`:

```text
Title: My First Project
Date: 2026-11

This is my project description. It can be as long as I like.

It can also contain multiple paragraphs.
```

The date must be in `YYYY-MM` format. Projects are listed newest first. Folder names don't appear on the site. Sharing permissions need to allow public viewing of each project folder and its files; check them if the sync cannot access them.

To embed a YouTube video, add an optional `YouTube:` line immediately after the date and before the blank line:

```text
Title: My First Project
Date: 2026-11
YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ

This is my project description.
```

Standard YouTube watch, share (`youtu.be`), Shorts, live, and embed links are supported. Omit the line entirely if there is no video. The video must permit embedding to play on the site.

To add captions, include either or both optional caption lines after the date and before the blank line. They can be used with or without the YouTube line:

```text
Title: My First Project
Date: 2026-11
Photo1 caption: The finished project
Photo2 caption: A look inside
YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ

This is my project description.
```

Each caption appears beneath its corresponding photo. Omit a caption line if you don't want one.

Google Docs are exported as plain text, so formatting such as bold text and links is not preserved. Make sure the document itself is viewable by anyone with the link and that viewers are allowed to download it.

## API and GitHub

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project and enable the **Google Drive API**.
2. Under APIs & Services > Credentials, create an API key. Restrict it to the Google Drive API. Don't use a browser-referrer restriction for this server-side workflow.
3. In your GitHub repository, go to Settings > Secrets and variables > Actions and add repository secrets named `GOOGLE_DRIVE_API_KEY` and `GOOGLE_DRIVE_FOLDER_ID` with the values above.
4. In Settings > Pages, set the build and deployment source to **GitHub Actions**.
5. Commit and push the workflow, script, and website changes. Under Actions, select **Sync projects from Google Drive** and choose **Run workflow** to sync on demand. Check its log if it fails.

The script validates all project folders before updating pages, so an incomplete folder causes the sync to fail instead of publishing a partial list. Removing a folder removes it from the next deployment. Do not use this for private information: published content may have been copied or cached.
