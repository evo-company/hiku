window.BENCHMARK_DATA = {
  "lastUpdate": 1773840845245,
  "repoUrl": "https://github.com/evo-company/hiku",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "kindritskiy.m@gmail.com",
            "name": "Kindritskiy Maksym",
            "username": "kindermax"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "6e9e5de4e6b23947d9f9041322c6b9a7555bcbb3",
          "message": "Merge pull request #209 from evo-company/setup-benchmarking\n\nadd codeflash, more bench commands to lets, write test for graph init…",
          "timestamp": "2026-03-18T15:29:47+02:00",
          "tree_id": "59ef5eb32f15f0d79647c914fcb97bfdc1548f0d",
          "url": "https://github.com/evo-company/hiku/commit/6e9e5de4e6b23947d9f9041322c6b9a7555bcbb3"
        },
        "date": 1773840622843,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 47.87898790346369,
            "unit": "iter/sec",
            "range": "stddev: 0.0035167910344531435",
            "extra": "mean: 20.885988693333623 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 17085.935299664867,
            "unit": "iter/sec",
            "range": "stddev: 0.000014407574720679008",
            "extra": "mean: 58.527671003156286 usec\nrounds: 3459"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8529.905482275693,
            "unit": "iter/sec",
            "range": "stddev: 0.000015492847202392123",
            "extra": "mean: 117.2345932880384 usec\nrounds: 5751"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6702.307124514291,
            "unit": "iter/sec",
            "range": "stddev: 0.00001943405247659722",
            "extra": "mean: 149.2023539688908 usec\nrounds: 4636"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3071.2695463125165,
            "unit": "iter/sec",
            "range": "stddev: 0.000021267633399518773",
            "extra": "mean: 325.5982534000111 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3120.915096647973,
            "unit": "iter/sec",
            "range": "stddev: 0.00001586905526160605",
            "extra": "mean: 320.4188416000335 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4779.099250971864,
            "unit": "iter/sec",
            "range": "stddev: 0.000013169505482896133",
            "extra": "mean: 209.2444512000128 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4904.064305771247,
            "unit": "iter/sec",
            "range": "stddev: 0.000012494751722816518",
            "extra": "mean: 203.9124973999975 usec\nrounds: 1000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "m.kindritskiy@smartweb.com.ua",
            "name": "m.kindritskiy"
          },
          "committer": {
            "email": "m.kindritskiy@smartweb.com.ua",
            "name": "m.kindritskiy"
          },
          "distinct": true,
          "id": "f9764f6b1530931cb6d77d0370cad38e3c127a2e",
          "message": "add memray to tests on CI",
          "timestamp": "2026-03-18T15:33:23+02:00",
          "tree_id": "b37ae047db294ff95733ae5d7a4a4ff91e7b34e7",
          "url": "https://github.com/evo-company/hiku/commit/f9764f6b1530931cb6d77d0370cad38e3c127a2e"
        },
        "date": 1773840844301,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 47.55402307066076,
            "unit": "iter/sec",
            "range": "stddev: 0.0035637731499766332",
            "extra": "mean: 21.02871503666672 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 16903.16331853674,
            "unit": "iter/sec",
            "range": "stddev: 0.000014154366491487925",
            "extra": "mean: 59.16052404838074 usec\nrounds: 3389"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8452.845773496325,
            "unit": "iter/sec",
            "range": "stddev: 0.000014820709626884835",
            "extra": "mean: 118.30335330800352 usec\nrounds: 5774"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6674.025381800462,
            "unit": "iter/sec",
            "range": "stddev: 0.000018406993809827153",
            "extra": "mean: 149.8346114665552 usec\nrounds: 4221"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3097.0475201810227,
            "unit": "iter/sec",
            "range": "stddev: 0.000015147561108541465",
            "extra": "mean: 322.88816799993754 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3117.6112515914647,
            "unit": "iter/sec",
            "range": "stddev: 0.000017903393824012692",
            "extra": "mean: 320.7584009999721 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4710.484445260484,
            "unit": "iter/sec",
            "range": "stddev: 0.000021564942582614224",
            "extra": "mean: 212.292389799984 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4903.742126331814,
            "unit": "iter/sec",
            "range": "stddev: 0.00001184102828402894",
            "extra": "mean: 203.92589460001602 usec\nrounds: 1000"
          }
        ]
      }
    ]
  }
}