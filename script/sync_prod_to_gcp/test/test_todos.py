import unittest
from script.sync_prod_to_gcp.sync_published_to_gcp import make_todos

class TestTodo(unittest.TestCase):
    def test_something(self):
        todos = make_todos("test/data/publish_240103.log", generate=True)
        self.assertEqual(878, len(todos))
        actions = sum([len(todo.get("actions")) for todo in todos])
        self.assertEqual(3038, actions)

        todos = make_todos("test/data/publish_240103.log", generate=False)
        self.assertEqual(878, len(todos))
        actions = sum([len(todo.get("actions")) for todo in todos])
        self.assertEqual(2309, actions)


if __name__ == '__main__':
    unittest.main()
