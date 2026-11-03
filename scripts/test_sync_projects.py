import unittest
from unittest.mock import patch

import sync_projects
from sync_projects import page, parse_details, project_photos


class ProjectVideoTests(unittest.TestCase):
    def details(self, fields=""):
        return f"Title: Project\nDate: 2026\n{fields}\nDescription\n".encode()

    def test_no_video_and_single_video(self):
        self.assertEqual(parse_details(self.details())[3], [])
        self.assertEqual(
            parse_details(self.details("YouTube: https://youtu.be/dQw4w9WgXcQ\n"))[3],
            ["dQw4w9WgXcQ"],
        )

    def test_multiple_videos_and_captions_are_rendered_in_order(self):
        details = self.details(
            "YouTube: https://youtu.be/dQw4w9WgXcQ\n"
            "Photo1 caption: First photo\n"
            "YouTube: https://www.youtube.com/watch?v=9bZkp7q19f0\n"
        )
        title, date, description, videos, captions = parse_details(details)
        result = page(title, date, description, ["one.jpg", "two.jpg"], videos, captions)
        self.assertEqual(videos, ["dQw4w9WgXcQ", "9bZkp7q19f0"])
        self.assertLess(result.index(videos[0]), result.index(videos[1]))
        self.assertEqual(result.count("<iframe "), 2)
        self.assertIn("First photo", result)

    def test_many_photos_sorted_and_captioned(self):
        items = [{"name": f"photo{n}.jpg"} for n in (10, 2, 1, 9, 8, 7, 6, 5, 4, 3)]
        photos = project_photos(items)
        self.assertEqual([p["name"] for p in photos], [f"photo{n}.jpg" for n in range(1, 11)])
        title, date, description, videos, captions = parse_details(self.details("Photo10 caption: Last photo\n"))
        result = page(title, date, description, [p["name"] for p in photos], videos, captions)
        self.assertEqual(result.count('<figure class="project-photo">'), 10)
        self.assertIn("Last photo", result)
        self.assertEqual(project_photos([]), [])

    def test_photo_gaps_and_duplicate_numbers_rejected(self):
        for names in (["photo2.jpg"], ["photo1.jpg", "photo3.png"], ["photo1.jpg", "PHOTO1.PNG"]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                project_photos([{"name": name} for name in names])

    def test_caption_without_photo_fails_sync(self):
        folder = {"name": "Example", "id": "folder", "mimeType": "application/vnd.google-apps.folder"}
        with patch.dict("os.environ", {"GOOGLE_DRIVE_API_KEY": "key", "GOOGLE_DRIVE_FOLDER_ID": "root"}), \
             patch.object(sync_projects, "children", side_effect=[[folder], []]), \
             patch.object(sync_projects, "download_details", return_value=self.details("Photo1 caption: Missing\n")):
            with self.assertRaisesRegex(ValueError, "caption.*existing photo"):
                sync_projects.main()

    def test_invalid_or_empty_video_and_duplicate_caption_rejected(self):
        for fields in (
            "YouTube: https://youtu.be/dQw4w9WgXcQ\nYouTube: invalid\n",
            "YouTube: \n",
            "Photo1 caption: One\nPhoto1 caption: Two\n",
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                parse_details(self.details(fields))


if __name__ == "__main__":
    unittest.main()
