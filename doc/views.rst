Writing views in Python
=======================

The couchdb-python package comes with a query server to allow you to
write views or update handlers in Python instead of JavaScript. When
couchdb-python is installed, it will install a script called couchpy
that runs the view server. To enable this for your CouchDB server, add
the following section to local.ini::

    [query_servers]
    python=/usr/bin/couchpy

After restarting CouchDB, the Futon view editor should show ``python`` in
the language pull-down menu. Here's some sample view code to get you started::

    def fun(doc):
        if 'date' in doc:
            yield doc['date'], doc

Note that the ``map`` function uses the Python ``yield`` keyword to emit
values, where JavaScript views use an ``emit()`` function.

Here's an example update handler code that will increment the
``field`` member of an existing document. The name of the ``field`` to
increment is passed in the query string::

    def fun(obj, req):
        field = req.query['field']
        if obj is not None and field in obj:
            obj[field] += 1
            return [obj, {"body": "incremented"}]
        else:
            return [None, {"body": "no such document or field"}]
