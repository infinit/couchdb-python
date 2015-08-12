# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from couchdb.util import StringIO
from couchdb import view
from couchdb.tests import testutil


class ViewServerTestCase(unittest.TestCase):

    def test_reset(self):
        input = StringIO(b'["reset"]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(), b'true\n')

    def test_add_fun(self):
        input = StringIO(b'["add_fun", "def fun(doc): yield None, doc"]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(), b'true\n')

    def test_map_doc(self):
        input = StringIO(b'["add_fun", "def fun(doc): yield None, doc"]\n'
                         b'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'true\n'
                         b'[[[null, {"foo": "bar"}]]]\n')

    def test_i18n(self):
        input = StringIO(b'["add_fun", "def fun(doc): yield doc[\\"test\\"], doc"]\n'
                         b'["map_doc", {"test": "b\xc3\xa5r"}]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'true\n'
                         b'[[["b\xc3\xa5r", {"test": "b\xc3\xa5r"}]]]\n')

    def test_map_doc_with_logging(self):
        fun = b'def fun(doc): log(\'running\'); yield None, doc'
        input = StringIO(b'["add_fun", "' + fun + b'"]\n'
                         b'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'true\n'
                         b'{"log": "running"}\n'
                         b'[[[null, {"foo": "bar"}]]]\n')

    def test_map_doc_with_logging_json(self):
        fun = b'def fun(doc): log([1, 2, 3]); yield None, doc'
        input = StringIO(b'["add_fun", "' + fun + b'"]\n'
                         b'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'true\n'
                         b'{"log": "[1, 2, 3]"}\n'
                         b'[[[null, {"foo": "bar"}]]]\n')

    def test_reduce(self):
        input = StringIO(b'["reduce", '
                          b'["def fun(keys, values): return sum(values)"], '
                          b'[[null, 1], [null, 2], [null, 3]]]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(), b'[true, [6]]\n')

    def test_reduce_with_logging(self):
        input = StringIO(b'["reduce", '
                          b'["def fun(keys, values): log(\'Summing %r\' % (values,)); return sum(values)"], '
                          b'[[null, 1], [null, 2], [null, 3]]]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'{"log": "Summing (1, 2, 3)"}\n'
                         b'[true, [6]]\n')

    def test_rereduce(self):
        input = StringIO(b'["rereduce", '
                          b'["def fun(keys, values, rereduce): return sum(values)"], '
                          b'[1, 2, 3]]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(), b'[true, [6]]\n')

    def test_reduce_empty(self):
        input = StringIO(b'["reduce", '
                          b'["def fun(keys, values): return sum(values)"], '
                          b'[]]\n')
        output = StringIO()
        view.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         b'[true, [0]]\n')

    def test_update(self):
        import json
        commands = [
            [
                'ddoc',
                'new',
                '_design/test_update',
                {
                    '_id': '_design/test_update',
                    '_rev': '8-d7379de23a751dc2a19e5638a7bbc5cc',
                    'language': 'python',
                    'updates': {
                        'inc': {
                            'map': '''\
def fun(obj, req):
    if obj is not None:
        obj['field'] += 1
    return [obj, {"body": "."}]
''',
                        }
                    }
                },
            ],
            [
                'ddoc',
                '_design/test_update',
                ['updates', 'inc'],
                [None, {}]
            ],
            [
                'ddoc',
                '_design/test_update',
                ['updates', 'inc'],
                [{'field': 41, 'other_field': 'x'}, {}]
            ],
        ]
        input = StringIO(b'\n'.join(json.dumps(c).encode('utf-8')
                                    for c in commands))
        output = StringIO()
        view.run(input=input, output=output)
        results = [
            json.loads(l.decode('utf-8'))
            for l in output.getvalue().strip().split(b'\n')
        ]
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], True)
        self.assertEqual(results[1], ['up', None, {'body': '.'}])
        self.assertEqual(
            results[2],
            ['up', {'field': 42, 'other_field': 'x'}, {'body': '.'}])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(testutil.doctest_suite(view))
    suite.addTest(unittest.makeSuite(ViewServerTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
