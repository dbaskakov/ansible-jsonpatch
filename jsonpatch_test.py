import json
import sys
import unittest

from jsonpatch import JSONPatcher, PathError


class TestJSONPatch(unittest.TestCase):
    """Ensure that `jsonpatch` conforms to RFC 6902."""

    def setUp(self):
        self.sample_json = json.dumps(
[
  {
    "foo": {
      "one": 1,
      "two": 2,
      "three": 3
    },
    "enabled": True
  },
  {
    "bar": {
      "one": 1,
      "two": 2,
      "three": 3
    },
    "enabled": False
  },
  {
    "baz": [
      {
        "foo": "apples",
        "bar": "oranges"
      },
      {
        "foo": "grapes",
        "bar": "oranges"
      },
      {
        "foo": "bananas",
        "bar": "potatoes"
      }
    ],
    "enabled": False
  }
])

    ## operation: add
    def test_op_add_foo_four(self):
        """Should add a `four` member to the first object."""
        patches = [
            {"op": "add", "path": "/0/foo/four", "value": 4}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[0]['foo']['four'], 4)

    def test_op_add_object_list(self):
        """Should add a new first object to the 'baz' list."""
        patches = [
            {"op": "add", "path": "/2/baz/0", "value": {"foo": "kiwis", "bar": "strawberries"}}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertDictEqual(jp.obj[2]['baz'][0], patches[0]['value'])

    def test_op_add_object_end_of_list(self):
        """Should add a new last object to the 'baz' list."""
        patches = [
            {"op": "add", "path": "/2/baz/-", "value": {"foo": "raspberries", "bar": "blueberries"}}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertDictEqual(jp.obj[2]['baz'][-1], patches[0]['value'])

    def test_op_add_replace_existing_value(self):
        """Should find an existing property and replace its value."""
        patches = [
            {"op": "add", "path": "/1/bar/three", "value": 10}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[1]['bar']['three'], 10)

    def test_op_add_ignore_existing_value(self):
        """Should ignore an existing property with the same value."""
        patches = [
            {"op": "add", "path": "/1/bar/one", "value": 1}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertFalse(changed)
        self.assertEqual(jp.obj[1]['bar']['one'], 1)

    ## operation: remove
    def test_op_remove_foo_three(self):
        """Should remove the 'three' member from the first object."""
        patches = [
            {"op": "remove", "path": "/0/foo/three"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertNotIn('three', jp.obj[0]['foo'])

    def test_op_remove_baz_list_member(self):
        """Should remove the last fruit item from the 'baz' list."""
        patches = [
            {"op": "remove", "path": "/2/baz/2"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        for obj in jp.obj[2]['baz']:
            self.assertNotEqual(obj['foo'], 'bananas')
            self.assertNotEqual(obj['bar'], 'potatoes')

    def test_op_remove_fail_on_nonexistent_member(self):
        """Should raise an exception if removing a non-existent object member."""
        patches = [
            {"op": "remove", "path": "/0/foo/four"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        self.assertRaises(PathError, jp.patch)

    ## operation: replace
    def test_op_replace_foo_three(self):
        """Should replace the value for the 'three' member in 'foo'."""
        patches = [
            {"op": "replace", "path": "/0/foo/three", "value": "booyah"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[0]['foo']['three'], 'booyah')

    def test_op_replace_fail_on_nonexistent_member(self):
        """Should raise an exception if replacing a non-existent object member."""
        patches = [
            {"op": "replace", "path": "/0/foo/four", "value": 4}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        self.assertRaises(PathError, jp.patch)

    ## operation: move
    def test_op_move_foo_three_bar_four(self):
        """Should move the 'three' property from 'foo' to 'bar'."""
        patches = [
            {"op": "move", "from": "/0/foo/three", "path": "/1/bar/four"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[0]['foo'].get('three', 'DUMMY VALUE'), 'DUMMY VALUE')
        self.assertEqual(jp.obj[1]['bar']['four'], 3)

    def test_op_move_baz_list_foo(self):
        """Should move the 'baz' list of fruits to 'foo' object."""
        patches = [
            {"op": "move", "from": "/2/baz", "path": "/0/foo/fruits"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[2].get('baz', 'DUMMY VALUE'), 'DUMMY VALUE')
        self.assertEqual(len(jp.obj[0]['foo']['fruits']), 3)

    def test_op_move_fail_on_nonexistent(self):
        """Should raise an exception if moving a non-existent object member."""
        patches = [
            {"op": "move", "from": "/0/foo/four", "path": "/1/bar/four"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        self.assertRaises(PathError, jp.patch)

    def test_op_move_foo_object_end_of_list(self):
        """Should move the 'three' member in 'foo' to the end of the 'baz' list."""
        patches = [
            {"op": "move", "from": "/0/foo/three", "path": "/2/baz/-"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[0]['foo'].get('three', 'DUMMY VALUE'), 'DUMMY VALUE')
        self.assertEqual(jp.obj[2]['baz'][-1], 3)

    ## operation: copy
    def test_op_copy_foo_three_bar_four(self):
        """Should copy the 'three' member in 'foo' to the 'bar' object."""
        patches = [
            {"op": "copy", "from": "/0/foo/three", "path": "/1/bar/four"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(jp.obj[0]['foo']['three'], 3)
        self.assertEqual(jp.obj[1]['bar']['four'], 3)

    def test_op_copy_baz_list_bar(self):
        """Should copy the 'baz' list of fruits to 'foo' object."""
        patches = [
            {"op": "copy", "from": "/2/baz", "path": "/0/foo/fruits"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        changed = jp.patch()
        self.assertTrue(changed)
        self.assertEqual(len(jp.obj[2]['baz']), 3)
        self.assertEqual(len(jp.obj[0]['foo']['fruits']), 3)

    def test_op_copy_fail_on_nonexistent_member(self):
        """Should raise an exception when copying a non-existent member."""
        patches = [
            {"op": "copy", "from": "/1/bar/four", "path": "/0/foo/fruits"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        self.assertRaises(PathError, jp.patch)

    ## operation: test
    def test_op_test_string_equal(self):
        """Should return True that two strings are equal."""
        patches = [
            {"op": "test", "path": "/2/baz/0/foo", "value": "apples"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertTrue(result)

    def test_op_test_string_unequal(self):
        """Should return False that two strings are unequal."""
        patches = [
            {"op": "test", "path": "/2/baz/0/foo", "value": "bananas"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertFalse(result)

    def test_op_test_number_equal(self):
        """Should return True that two numbers are equal."""
        patches = [
            {"op": "test", "path": "/0/foo/one", "value": 1}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertTrue(result)

    def test_op_test_number_unequal(self):
        """Should return False that two numbers are unequal."""
        patches = [
            {"op": "test", "path": "/0/foo/one", "value": "bananas"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertFalse(result)

    def test_op_test_list_equal(self):
        """Should return True that two lists are equal."""
        patches = [
            {"op": "add", "path": "/0/foo/compare", "value": [1, 2, 3]},
            {"op": "test", "path": "/0/foo/compare", "value": [1, 2, 3]}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertTrue(result)

    def test_op_test_wildcard(self):
        """Should find an element in the 'baz' list with the matching value."""
        patches = [
            {"op": "test", "path": "/2/baz/*/foo", "value": "grapes"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertTrue(result)

    def test_op_test_wildcard_not_found(self):
        """Should return False on not finding an element with the given value."""
        patches = [
            {"op": "test", "path": "/2/baz/*/bar", "value": "rocks"}
        ]
        jp = JSONPatcher(self.sample_json, *patches)
        result = jp.patch()
        self.assertFalse(result)

  
if __name__ == "__main__":
    unittest.main()
