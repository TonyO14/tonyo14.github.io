# Project sync setup

The workflow runs on pushes to `main` and can also be run manually from GitHub's Actions tab. It generates the site and deploys it directly to GitHub Pages; generated files are not committed to the repository. Local changes must be committed and pushed before they can be published.

## Google Drive

1. Create a folder for your projects. Under Share, set General access to **Anyone with the link**, Viewer. Everything in this folder will be published, so don't put private information in it.
2. Copy the folder ID from its URL: `https://drive.google.com/drive/folders/FOLDER_ID`.
3. Create a separate subfolder inside it for each project. In each project folder, upload exactly these three files (ordinary uploaded files, not Google Docs):
   - `details.txt` (UTF-8 encoded)
   - `photo1.jpg` or `photo1.png`
   - `photo2.jpg` or `photo2.png`

Example `details.txt`:

```text
Title: My First Project
Date: 2026-11

This is my project description. It can be as long as I like.

It can also contain multiple paragraphs.
```

The date must be in `YYYY-MM` format. Projects are listed newest first. Folder names don't appear on the site. Sharing permissions need to allow public viewing of each project folder and its files; check them if the sync cannot access them.

## API and GitHub

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project and enable the **Google Drive API**.
2. Under APIs & Services > Credentials, create an API key. Restrict it to the Google Drive API. Don't use a browser-referrer restriction for this server-side workflow.
3. In your GitHub repository, go to Settings > Secrets and variables > Actions and add repository secrets named `GOOGLE_DRIVE_API_KEY` and `GOOGLE_DRIVE_FOLDER_ID` with the values above.
4. In Settings > Pages, set the build and deployment source to **GitHub Actions**.
5. Commit and push the workflow, script, and website changes. Under Actions, select **Sync projects from Google Drive** and choose **Run workflow** to sync on demand. Check its log if it fails.

The script validates all project folders before updating pages, so an incomplete folder causes the sync to fail instead of publishing a partial list. Removing a folder removes it from the next deployment. Do not use this for private information: published content may have been copied or cached.
