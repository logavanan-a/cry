"""TestCase Practise."""
import unittest


class TestCase(unittest.TestCase):

    def setUp(self):
        self.Foo = 'Foo'

    def tearDown(self):
        self.Foo = ''

    def test_upper(self):
        self.assertEqual(self.Foo, 'Foo')

    def test_isupper(self):
        self.assertTrue(self.Foo.istitle())
        self.assertFalse(self.Foo.isupper())
        self.assertTrue(self.Foo.isupper())


if __name__ == '__main__':
    unittest.main()
