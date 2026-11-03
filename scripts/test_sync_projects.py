import unittest

from sync_projects import page, parse_details


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
