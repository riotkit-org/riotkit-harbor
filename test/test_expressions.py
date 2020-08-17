from rkd_harbor.expressions import safe_eval
from rkd_harbor.test import BaseHarborTestClass


class SafeEvalTests(BaseHarborTestClass):
    """author: https://stackoverflow.com/a/48135793/6782994
    """

    def test_basic(self):
        self.assertEqual(safe_eval("1", {}), 1)

    def test_local(self):
        self.assertEqual(safe_eval("a", {'a': 2}), 2)

    def test_local_bool(self):
        self.assertEqual(safe_eval("a==2", {'a': 2}), True)

    def test_lambda(self):
        self.assertRaises(ValueError, safe_eval, "lambda : None", {'a': 2})

    def test_bad_name(self):
        self.assertRaises(ValueError, safe_eval, "a == None2", {'a': 2})

    def test_attr(self):
        self.assertRaises(AttributeError, safe_eval, "a.__dict__", {'a': 2})

    def test_eval(self):
        self.assertRaises(ValueError, safe_eval, "eval('os.exit()')", {})

    def test_exec(self):
        self.assertRaises(SyntaxError, safe_eval, "exec 'import os'", {})

    def test_multiply(self):
        self.assertRaises(ValueError, safe_eval, "'s' * 3", {})

    def test_power(self):
        self.assertRaises(ValueError, safe_eval, "3 ** 3", {})

    def test_comprehensions(self):
        self.assertRaises(ValueError, safe_eval, "[i for i in [1,2]]", {'i': 1})

    def test_pattern_to_lookup_labels(self):
        self.assertTrue(
            safe_eval(
                '"org.riotkit.useMaintenanceMode" in service["labels"] and service["labels"]["org.riotkit.useMaintenanceMode"]', {
                    "service": {
                        'labels': {
                            'org.riotkit.useMaintenanceMode': True
                        }
                    }
                }
            )
        )

    def test_python36_nameconstant(self):
        """In Python 3.8 the 'True' is classified as Constant, in Python 3.6 as a NameConstant"""

        self.assertTrue(safe_eval('True', {}))

    def test_pattern_using_basic_string_functions(self):
        self.assertTrue(safe_eval('"org.riotkit.replicas".startswith("org.riotkit")', {}))
