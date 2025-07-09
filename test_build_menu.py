import unittest
from build import build_menu, rel_link

class TestMenuLinks(unittest.TestCase):
    def setUp(self):
        self.menu = [
            {'name': 'Home', 'url': 'index.html', 'weight': 10},
            {'name': 'News', 'url': 'news/_index.html', 'weight': 20},
            {'name': 'About', 'url': 'about.html', 'weight': 30},
        ]

    def test_homepage_menu(self):
        # On homepage (docs/index.html)
        current_output_path = 'index.html'
        html = build_menu(self.menu, current_output_path)
        self.assertIn('href="index.html"', html)
        self.assertIn('href="news/index.html"', html)
        self.assertIn('href="about/index.html"', html)

    def test_about_menu(self):
        # On about page (docs/about/index.html)
        current_output_path = 'about/index.html'
        html = build_menu(self.menu, current_output_path)
        self.assertIn('href="../index.html"', html)
        self.assertIn('href="../news/index.html"', html)
        self.assertIn('href="index.html"', html)

    def test_news_index_menu(self):
        # On news index (docs/news/index.html)
        current_output_path = 'news/index.html'
        html = build_menu(self.menu, current_output_path)
        self.assertIn('href="../index.html"', html)
        self.assertIn('href="index.html"', html)
        self.assertIn('href="../about/index.html"', html)

    def test_news_article_menu(self):
        # On news article (docs/news/2025-07-08-launching-open-physics-ed.html)
        current_output_path = 'news/2025-07-08-launching-open-physics-ed.html'
        html = build_menu(self.menu, current_output_path)
        self.assertIn('href="../index.html"', html)
        self.assertIn('href="index.html"', html)
        self.assertIn('href="../about/index.html"', html)

if __name__ == '__main__':
    unittest.main()
