from __future__ import unicode_literals

from hiku.edn import loads
from hiku.query import Node
from hiku.result import Index, Proxy, Reference, ROOT
from hiku.writers.simple import dumps


def check_writes(data, output):
    first = loads(dumps(data))
    second = loads(output)
    assert first == second


def test_simple():
    index = Index()
    index.root['f1'] = 1
    index.root['a'] = {'f2': 2}
    index['b'][1].update({'f3': 'bar1'})
    index['b'][2].update({'f3': 'bar2'})
    index['b'][3].update({'f3': 'bar3'})
    index.root['l1'] = Reference('b', 1)
    index.root['l2'] = [Reference('b', 2), Reference('b', 3)]
    index.finish()

    result = Proxy(index, ROOT, Node([]))
    check_writes(
        result,
        """
        {
          "f1" 1
          "a" {"f2" 2}
          "b" {1 {"f3" "bar1"}
               2 {"f3" "bar2"}
               3 {"f3" "bar3"}}
          "l1" #graph/ref ["b" 1]
          "l2" [#graph/ref ["b" 2]
                #graph/ref ["b" 3]]
        }
        """,
    )
