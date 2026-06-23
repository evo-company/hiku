window.BENCHMARK_DATA = {
  "lastUpdate": 1782210765066,
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
      },
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
          "id": "400bf10ffd6d62268b0c92cb811aa45bdb86d013",
          "message": "Merge pull request #208 from evo-company/codeflash/setup-github-actions-1773831995823\n\nAdd CodeFlash GitHub Actions workflow",
          "timestamp": "2026-03-18T15:37:09+02:00",
          "tree_id": "6cd23df7c0cec2bcbedf98f0c85bf97f6eed83e0",
          "url": "https://github.com/evo-company/hiku/commit/400bf10ffd6d62268b0c92cb811aa45bdb86d013"
        },
        "date": 1773841065390,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 48.854727846507444,
            "unit": "iter/sec",
            "range": "stddev: 0.002808429389872338",
            "extra": "mean: 20.468848033332943 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 16914.235966097334,
            "unit": "iter/sec",
            "range": "stddev: 0.000015121067084612808",
            "extra": "mean: 59.12179551026641 usec\nrounds: 3252"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8356.372808953496,
            "unit": "iter/sec",
            "range": "stddev: 0.000015592537515071548",
            "extra": "mean: 119.6691462746304 usec\nrounds: 5852"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6618.342838654941,
            "unit": "iter/sec",
            "range": "stddev: 0.00001836445793803896",
            "extra": "mean: 151.09522494957847 usec\nrounds: 4441"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3038.961039514058,
            "unit": "iter/sec",
            "range": "stddev: 0.000016082393301493972",
            "extra": "mean: 329.05982899994797 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3067.955123143077,
            "unit": "iter/sec",
            "range": "stddev: 0.000015199713760255052",
            "extra": "mean: 325.9500089999733 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4685.773724354495,
            "unit": "iter/sec",
            "range": "stddev: 0.000012750847363553566",
            "extra": "mean: 213.41192699990188 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4812.518504853159,
            "unit": "iter/sec",
            "range": "stddev: 0.00001769250237073969",
            "extra": "mean: 207.79140880010232 usec\nrounds: 1000"
          }
        ]
      },
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
          "id": "5f24665dd367d2b176b46215015204cd2a19fe01",
          "message": "Merge pull request #210 from evo-company/optimize-types-creation\n\nperf: optimize types creation",
          "timestamp": "2026-03-19T16:59:09+02:00",
          "tree_id": "fb38121b4f8e2d453bc74f5c0ec1c506e5fd262d",
          "url": "https://github.com/evo-company/hiku/commit/5f24665dd367d2b176b46215015204cd2a19fe01"
        },
        "date": 1773932392392,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 30.58673289418906,
            "unit": "iter/sec",
            "range": "stddev: 0.0035621154290615166",
            "extra": "mean: 32.693913516666655 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 133126.93156343565,
            "unit": "iter/sec",
            "range": "stddev: 3.8095199695269943e-7",
            "extra": "mean: 7.511628100009915 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 283862.1017205964,
            "unit": "iter/sec",
            "range": "stddev: 2.8547568124747676e-7",
            "extra": "mean: 3.5228373000080637 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 116743.13595033789,
            "unit": "iter/sec",
            "range": "stddev: 6.756821425063433e-7",
            "extra": "mean: 8.565814099986113 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 9603.38364189113,
            "unit": "iter/sec",
            "range": "stddev: 0.000010671786616312567",
            "extra": "mean: 104.12996473845719 usec\nrounds: 2524"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 4743.3683477648465,
            "unit": "iter/sec",
            "range": "stddev: 0.000014813777795535329",
            "extra": "mean: 210.82065036572936 usec\nrounds: 2597"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 3710.1390606711075,
            "unit": "iter/sec",
            "range": "stddev: 0.000017775780890643887",
            "extra": "mean: 269.53167621138044 usec\nrounds: 2270"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 1718.4159625984505,
            "unit": "iter/sec",
            "range": "stddev: 0.000021915382965218768",
            "extra": "mean: 581.9312796000105 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 1741.707609544754,
            "unit": "iter/sec",
            "range": "stddev: 0.00002129656169426929",
            "extra": "mean: 574.1491824000121 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 2825.3380716754186,
            "unit": "iter/sec",
            "range": "stddev: 0.00001641130329383719",
            "extra": "mean: 353.9399443999997 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 2984.3431759337623,
            "unit": "iter/sec",
            "range": "stddev: 0.0001851093147006813",
            "extra": "mean: 335.0821072000585 usec\nrounds: 1000"
          }
        ]
      },
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
          "id": "2f399975063a596c7095d63e2546293706e2b660",
          "message": "Merge pull request #214 from evo-company/codspeed-wizard-1773993348212\n\nAdd CodSpeed continuous performance testing",
          "timestamp": "2026-03-20T15:16:41+02:00",
          "tree_id": "ca5538312399d7fa938181ebf61bc4273de0d865",
          "url": "https://github.com/evo-company/hiku/commit/2f399975063a596c7095d63e2546293706e2b660"
        },
        "date": 1774012646257,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 30.093803015970728,
            "unit": "iter/sec",
            "range": "stddev: 0.0031148124056680788",
            "extra": "mean: 33.229432633333246 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 118402.15253176213,
            "unit": "iter/sec",
            "range": "stddev: 0.000002511295761800084",
            "extra": "mean: 8.445792400030427 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 279937.45637424546,
            "unit": "iter/sec",
            "range": "stddev: 3.4371113301099166e-7",
            "extra": "mean: 3.5722264999904496 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 119657.95868208847,
            "unit": "iter/sec",
            "range": "stddev: 3.8988073216594503e-7",
            "extra": "mean: 8.35715410001967 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 8582.738928836718,
            "unit": "iter/sec",
            "range": "stddev: 0.000012426341926091056",
            "extra": "mean: 116.51292300644842 usec\nrounds: 2182"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 4235.35410873154,
            "unit": "iter/sec",
            "range": "stddev: 0.000018657957514476827",
            "extra": "mean: 236.1077667481016 usec\nrounds: 2045"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 3299.2054913207517,
            "unit": "iter/sec",
            "range": "stddev: 0.00002224981484466674",
            "extra": "mean: 303.10327823796024 usec\nrounds: 2293"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 1553.5001990504013,
            "unit": "iter/sec",
            "range": "stddev: 0.00002054388984512668",
            "extra": "mean: 643.7076742000187 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 1564.7501199632368,
            "unit": "iter/sec",
            "range": "stddev: 0.000027340847796932262",
            "extra": "mean: 639.0796761999894 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 2475.680077536874,
            "unit": "iter/sec",
            "range": "stddev: 0.00016852735485085708",
            "extra": "mean: 403.9294127999483 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 2626.7267981795358,
            "unit": "iter/sec",
            "range": "stddev: 0.000015141976511854164",
            "extra": "mean: 380.7019446000453 usec\nrounds: 1000"
          }
        ]
      },
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
          "id": "f71e1d2a861c75ffe8ab7208272653c0b4771019",
          "message": "Merge pull request #213 from evo-company/codex/identify-querytime-allocation-hotps\n\nperf: optimize InitOptions copying",
          "timestamp": "2026-03-20T15:25:07+02:00",
          "tree_id": "2d77ad281ef28cf3b74212a4db0f06a55277e326",
          "url": "https://github.com/evo-company/hiku/commit/f71e1d2a861c75ffe8ab7208272653c0b4771019"
        },
        "date": 1774013148822,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 29.552487564431264,
            "unit": "iter/sec",
            "range": "stddev: 0.0036451788346915375",
            "extra": "mean: 33.838099003333255 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 129077.6334328912,
            "unit": "iter/sec",
            "range": "stddev: 8.241221496818487e-7",
            "extra": "mean: 7.74727559999704 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 278585.4511717496,
            "unit": "iter/sec",
            "range": "stddev: 3.704343722848713e-7",
            "extra": "mean: 3.5895628999789153 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 120206.86688235826,
            "unit": "iter/sec",
            "range": "stddev: 4.665569768547057e-7",
            "extra": "mean: 8.318992299987826 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 8551.853002348089,
            "unit": "iter/sec",
            "range": "stddev: 0.000012245346757814218",
            "extra": "mean: 116.93372181741539 usec\nrounds: 2333"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 4260.656202060597,
            "unit": "iter/sec",
            "range": "stddev: 0.000017397083691334593",
            "extra": "mean: 234.70563044170666 usec\nrounds: 3101"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 3314.9678383417345,
            "unit": "iter/sec",
            "range": "stddev: 0.000021039041528252228",
            "extra": "mean: 301.6620518708368 usec\nrounds: 2352"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 1597.950766460689,
            "unit": "iter/sec",
            "range": "stddev: 0.000023009122284697687",
            "extra": "mean: 625.8015083999779 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 1603.3639488924032,
            "unit": "iter/sec",
            "range": "stddev: 0.0000400810957156385",
            "extra": "mean: 623.6887143999936 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 2588.0586851148355,
            "unit": "iter/sec",
            "range": "stddev: 0.00015330668149667411",
            "extra": "mean: 386.3900017999896 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 2743.7455981610706,
            "unit": "iter/sec",
            "range": "stddev: 0.000014770479627022163",
            "extra": "mean: 364.46527719998016 usec\nrounds: 1000"
          }
        ]
      },
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
          "id": "b4c9bb4e1d8392b782c02f56b7e3ec4c18430aa6",
          "message": "Merge pull request #215 from evo-company/add-engine-comprehensive-benchmark\n\nAdd comprehensive benchmark for engine execution",
          "timestamp": "2026-03-20T16:35:32+02:00",
          "tree_id": "469b796c2b894fe03eb4eaba077dec77e3a5a502",
          "url": "https://github.com/evo-company/hiku/commit/b4c9bb4e1d8392b782c02f56b7e3ec4c18430aa6"
        },
        "date": 1774017440524,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 1664.5287875052113,
            "unit": "iter/sec",
            "range": "stddev: 0.00017968402612138383",
            "extra": "mean: 600.7706250000012 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 976.4021391072068,
            "unit": "iter/sec",
            "range": "stddev: 0.000035576972398440265",
            "extra": "mean: 1.0241681781999885 msec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 210.84964972340268,
            "unit": "iter/sec",
            "range": "stddev: 0.0005328635216276138",
            "extra": "mean: 4.742715965199954 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 714.5253628259921,
            "unit": "iter/sec",
            "range": "stddev: 0.0000524095041850411",
            "extra": "mean: 1.399530446400024 msec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 264.9327851869294,
            "unit": "iter/sec",
            "range": "stddev: 0.0003346262661674147",
            "extra": "mean: 3.7745422836000726 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 199.14337405462265,
            "unit": "iter/sec",
            "range": "stddev: 0.00042248086961307137",
            "extra": "mean: 5.021507769200054 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 161.6953622336933,
            "unit": "iter/sec",
            "range": "stddev: 0.0006217594794179432",
            "extra": "mean: 6.184469277199992 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 29.064358333836743,
            "unit": "iter/sec",
            "range": "stddev: 0.003231662464984242",
            "extra": "mean: 34.40640211333341 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 114668.4342728704,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023154991333755763",
            "extra": "mean: 8.720795800005021 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 273656.8701872395,
            "unit": "iter/sec",
            "range": "stddev: 2.912216951081654e-7",
            "extra": "mean: 3.6542112000176985 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 115399.69723793141,
            "unit": "iter/sec",
            "range": "stddev: 3.416482978387315e-7",
            "extra": "mean: 8.665533999956665 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 8483.10275517456,
            "unit": "iter/sec",
            "range": "stddev: 0.000013700112686254814",
            "extra": "mean: 117.88139656684173 usec\nrounds: 3379"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 4167.672185977744,
            "unit": "iter/sec",
            "range": "stddev: 0.000021270980177153348",
            "extra": "mean: 239.94209606132875 usec\nrounds: 2082"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 3184.2028125684137,
            "unit": "iter/sec",
            "range": "stddev: 0.0004876871706381397",
            "extra": "mean: 314.0503475635677 usec\nrounds: 2319"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 1605.6893303305196,
            "unit": "iter/sec",
            "range": "stddev: 0.00002354878684529875",
            "extra": "mean: 622.7854798002284 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 1627.383766883479,
            "unit": "iter/sec",
            "range": "stddev: 0.00001813471850683413",
            "extra": "mean: 614.4832093999867 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 2640.4129547554303,
            "unit": "iter/sec",
            "range": "stddev: 0.000015678865580824828",
            "extra": "mean: 378.7286372000949 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 2752.3638551740423,
            "unit": "iter/sec",
            "range": "stddev: 0.000014717027021170623",
            "extra": "mean: 363.3240561999628 usec\nrounds: 1000"
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
          "id": "d926335df4d3943fe0c38a147e7d5f5ce65db233",
          "message": "disable memray if not CI test job",
          "timestamp": "2026-03-20T17:31:53+02:00",
          "tree_id": "738d8e7fc6930799f6fc8cb2cfd1827ac10ecac9",
          "url": "https://github.com/evo-company/hiku/commit/d926335df4d3943fe0c38a147e7d5f5ce65db233"
        },
        "date": 1774020780998,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3066.157138805791,
            "unit": "iter/sec",
            "range": "stddev: 0.0001340613175733462",
            "extra": "mean: 326.1411449999855 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1928.1236160775773,
            "unit": "iter/sec",
            "range": "stddev: 0.00005695607245820774",
            "extra": "mean: 518.6389459999049 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 453.36526324191675,
            "unit": "iter/sec",
            "range": "stddev: 0.00045967294623102143",
            "extra": "mean: 2.2057269956000085 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1413.105533960959,
            "unit": "iter/sec",
            "range": "stddev: 0.0000248487563639153",
            "extra": "mean: 707.6612298000015 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 580.2372938390547,
            "unit": "iter/sec",
            "range": "stddev: 0.0003408306921998493",
            "extra": "mean: 1.7234328275999757 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 422.2324515220941,
            "unit": "iter/sec",
            "range": "stddev: 0.0003496542994611418",
            "extra": "mean: 2.3683636735999984 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 345.6425247026552,
            "unit": "iter/sec",
            "range": "stddev: 0.0005286159157977052",
            "extra": "mean: 2.8931625263999763 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 63.69418672843361,
            "unit": "iter/sec",
            "range": "stddev: 0.0031430520425483775",
            "extra": "mean: 15.700019913333659 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 352505.235318843,
            "unit": "iter/sec",
            "range": "stddev: 1.674807626873156e-7",
            "extra": "mean: 2.836837300006323 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 713267.9318994781,
            "unit": "iter/sec",
            "range": "stddev: 1.1509218859624915e-7",
            "extra": "mean: 1.4019976999904316 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 313546.5006392094,
            "unit": "iter/sec",
            "range": "stddev: 1.644494559151775e-7",
            "extra": "mean: 3.1893195999998625 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 17125.25734214084,
            "unit": "iter/sec",
            "range": "stddev: 0.00001251931480663397",
            "extra": "mean: 58.393283091825886 usec\nrounds: 5175"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8487.161551720623,
            "unit": "iter/sec",
            "range": "stddev: 0.00001586047966162954",
            "extra": "mean: 117.82502240660986 usec\nrounds: 6025"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6697.927382929423,
            "unit": "iter/sec",
            "range": "stddev: 0.00001968865789463517",
            "extra": "mean: 149.29991665013202 usec\nrounds: 4991"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3095.881711650172,
            "unit": "iter/sec",
            "range": "stddev: 0.0000165579990787618",
            "extra": "mean: 323.0097571999863 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 2889.8773566681657,
            "unit": "iter/sec",
            "range": "stddev: 0.00016034770823539476",
            "extra": "mean: 346.03544600001044 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4538.903710779552,
            "unit": "iter/sec",
            "range": "stddev: 0.000012747458932428181",
            "extra": "mean: 220.31751800001302 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4670.5065429244305,
            "unit": "iter/sec",
            "range": "stddev: 0.00001387809146700216",
            "extra": "mean: 214.1095384000579 usec\nrounds: 1000"
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
          "id": "474346ebf71673319ba24f0bd2906b4e73e6029a",
          "message": "add lets test-memray",
          "timestamp": "2026-03-20T18:31:31+02:00",
          "tree_id": "47b479ad5c326ad35fe1dab6a7253536e20fb415",
          "url": "https://github.com/evo-company/hiku/commit/474346ebf71673319ba24f0bd2906b4e73e6029a"
        },
        "date": 1774024355626,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3221.506978518485,
            "unit": "iter/sec",
            "range": "stddev: 0.0001407922798206032",
            "extra": "mean: 310.4137307999508 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1957.4830239791615,
            "unit": "iter/sec",
            "range": "stddev: 0.0000254808597148286",
            "extra": "mean: 510.8601135999664 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 467.8753320687365,
            "unit": "iter/sec",
            "range": "stddev: 0.00040259486034094203",
            "extra": "mean: 2.1373214860002236 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1490.3269952303726,
            "unit": "iter/sec",
            "range": "stddev: 0.000020368742675239617",
            "extra": "mean: 670.993683399945 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 587.6249282429634,
            "unit": "iter/sec",
            "range": "stddev: 0.0003210435558536312",
            "extra": "mean: 1.701765789599949 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 438.1348016077079,
            "unit": "iter/sec",
            "range": "stddev: 0.00037288066448120234",
            "extra": "mean: 2.2824025764001474 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 362.4067532099019,
            "unit": "iter/sec",
            "range": "stddev: 0.0005713763375498637",
            "extra": "mean: 2.7593304792000137 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 63.82107709638885,
            "unit": "iter/sec",
            "range": "stddev: 0.00299109093676031",
            "extra": "mean: 15.668804813333093 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 355333.9661251506,
            "unit": "iter/sec",
            "range": "stddev: 2.0526417042657615e-7",
            "extra": "mean: 2.8142539000839406 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 727702.9982277224,
            "unit": "iter/sec",
            "range": "stddev: 1.796043517683578e-7",
            "extra": "mean: 1.374186999964877 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 312107.9241714764,
            "unit": "iter/sec",
            "range": "stddev: 2.8455480955639357e-7",
            "extra": "mean: 3.2040199000221037 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 17212.945675337694,
            "unit": "iter/sec",
            "range": "stddev: 0.000010692241525684235",
            "extra": "mean: 58.09580875124568 usec\nrounds: 5119"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8434.34051300271,
            "unit": "iter/sec",
            "range": "stddev: 0.00001523113567573308",
            "extra": "mean: 118.56291531725104 usec\nrounds: 5928"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6653.7348764576445,
            "unit": "iter/sec",
            "range": "stddev: 0.000019451417476748572",
            "extra": "mean: 150.29153078193974 usec\nrounds: 4938"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3126.1865323754596,
            "unit": "iter/sec",
            "range": "stddev: 0.000015213801368525117",
            "extra": "mean: 319.8785451999697 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3118.775254012807,
            "unit": "iter/sec",
            "range": "stddev: 0.00014359484037473487",
            "extra": "mean: 320.63868620008407 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4901.598027616443,
            "unit": "iter/sec",
            "range": "stddev: 0.00001239119337786294",
            "extra": "mean: 204.01509759997225 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 5033.978934953794,
            "unit": "iter/sec",
            "range": "stddev: 0.000011910929912110511",
            "extra": "mean: 198.65001680011574 usec\nrounds: 1000"
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
          "id": "b96b94cb6857f25f61ba3032ac1b42c5fd8ea3f7",
          "message": "Add denormalize benchmarks, update dev docs",
          "timestamp": "2026-03-20T18:43:41+02:00",
          "tree_id": "3d60cfa18aa3adbc3e555d1d21de75d15e0ce9be",
          "url": "https://github.com/evo-company/hiku/commit/b96b94cb6857f25f61ba3032ac1b42c5fd8ea3f7"
        },
        "date": 1774025148172,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 63923.56182077867,
            "unit": "iter/sec",
            "range": "stddev: 7.175404797616447e-7",
            "extra": "mean: 15.643683979996013 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1360.688614795988,
            "unit": "iter/sec",
            "range": "stddev: 0.000018507513096000726",
            "extra": "mean: 734.9220013499803 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1337.5395773263897,
            "unit": "iter/sec",
            "range": "stddev: 0.000016382684725406003",
            "extra": "mean: 747.64142829994 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1349.6376723531748,
            "unit": "iter/sec",
            "range": "stddev: 0.00002143035604367377",
            "extra": "mean: 740.9396021499902 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 130.4159815912994,
            "unit": "iter/sec",
            "range": "stddev: 0.0004802949833995419",
            "extra": "mean: 7.667771907999918 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3341.7075388086114,
            "unit": "iter/sec",
            "range": "stddev: 0.000022487911556812187",
            "extra": "mean: 299.24821019990304 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2005.2613767263292,
            "unit": "iter/sec",
            "range": "stddev: 0.00001565856165856784",
            "extra": "mean: 498.68810700006634 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 475.73538708483716,
            "unit": "iter/sec",
            "range": "stddev: 0.0003819612186422256",
            "extra": "mean: 2.102008862800176 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1521.6037745168478,
            "unit": "iter/sec",
            "range": "stddev: 0.000021817697326583224",
            "extra": "mean: 657.2013140001104 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 606.541614587774,
            "unit": "iter/sec",
            "range": "stddev: 0.00023409086730137173",
            "extra": "mean: 1.648691492799935 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 449.3651423821367,
            "unit": "iter/sec",
            "range": "stddev: 0.00040540964509702324",
            "extra": "mean: 2.225361750799993 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 377.25730212847014,
            "unit": "iter/sec",
            "range": "stddev: 0.00034836179355992436",
            "extra": "mean: 2.650710786399736 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 64.11861292287874,
            "unit": "iter/sec",
            "range": "stddev: 0.002855404505092465",
            "extra": "mean: 15.596095336665977 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 348927.1919220066,
            "unit": "iter/sec",
            "range": "stddev: 1.7096013845647052e-7",
            "extra": "mean: 2.865927400188184 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 713564.2498118454,
            "unit": "iter/sec",
            "range": "stddev: 1.5129254967539782e-7",
            "extra": "mean: 1.4014155000950268 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 309560.7497118733,
            "unit": "iter/sec",
            "range": "stddev: 1.603508860478392e-7",
            "extra": "mean: 3.2303836999062696 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 17495.353999152623,
            "unit": "iter/sec",
            "range": "stddev: 0.000010652059121012924",
            "extra": "mean: 57.158031786520844 usec\nrounds: 5474"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8612.079210256254,
            "unit": "iter/sec",
            "range": "stddev: 0.000015580158296387906",
            "extra": "mean: 116.11597798695173 usec\nrounds: 5860"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6764.746837709681,
            "unit": "iter/sec",
            "range": "stddev: 0.000019036618972320886",
            "extra": "mean: 147.82519198287795 usec\nrounds: 4615"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3142.5189539463063,
            "unit": "iter/sec",
            "range": "stddev: 0.00012741563495444175",
            "extra": "mean: 318.21605999996336 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3218.4360399744623,
            "unit": "iter/sec",
            "range": "stddev: 0.000014838667252858304",
            "extra": "mean: 310.709918600071 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4944.5514147555905,
            "unit": "iter/sec",
            "range": "stddev: 0.000011833235773735229",
            "extra": "mean: 202.24281560017516 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 5146.53177477982,
            "unit": "iter/sec",
            "range": "stddev: 0.00001160119423068329",
            "extra": "mean: 194.30561079996096 usec\nrounds: 1000"
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
          "id": "39c4a6f2da10231dbbe50094f3b7429579b399d2",
          "message": "Add benchmarks for validation",
          "timestamp": "2026-03-20T18:54:29+02:00",
          "tree_id": "c99f6704e3beeab5675db97b837efd62d5421c44",
          "url": "https://github.com/evo-company/hiku/commit/39c4a6f2da10231dbbe50094f3b7429579b399d2"
        },
        "date": 1774025815684,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 63417.943820563014,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017765828355408428",
            "extra": "mean: 15.76840779999799 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1378.857066297434,
            "unit": "iter/sec",
            "range": "stddev: 0.000036385522346988496",
            "extra": "mean: 725.2383328500051 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1366.4960767787582,
            "unit": "iter/sec",
            "range": "stddev: 0.00002868071616394495",
            "extra": "mean: 731.7986615499844 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1378.4704774650884,
            "unit": "iter/sec",
            "range": "stddev: 0.000023518531778063723",
            "extra": "mean: 725.441724250004 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.55293652102088,
            "unit": "iter/sec",
            "range": "stddev: 0.0004519735734667866",
            "extra": "mean: 7.601502683599994 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3324.1218040003855,
            "unit": "iter/sec",
            "range": "stddev: 0.00001788024619387639",
            "extra": "mean: 300.83133499998667 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1993.223679712306,
            "unit": "iter/sec",
            "range": "stddev: 0.00001711211171344069",
            "extra": "mean: 501.6998394000296 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 468.1619702193173,
            "unit": "iter/sec",
            "range": "stddev: 0.00045812110332747323",
            "extra": "mean: 2.1360128835999546 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1507.9250721199408,
            "unit": "iter/sec",
            "range": "stddev: 0.000016460037927782315",
            "extra": "mean: 663.1629240000194 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 596.8833463414684,
            "unit": "iter/sec",
            "range": "stddev: 0.00022568136510090996",
            "extra": "mean: 1.6753692427999398 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 440.1218309549701,
            "unit": "iter/sec",
            "range": "stddev: 0.0004227614044679345",
            "extra": "mean: 2.272098154800034 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 366.40427103567214,
            "unit": "iter/sec",
            "range": "stddev: 0.0004064027834724879",
            "extra": "mean: 2.7292258279998123 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 62.43453484081042,
            "unit": "iter/sec",
            "range": "stddev: 0.003355229638741092",
            "extra": "mean: 16.01677665333303 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 351711.45254254265,
            "unit": "iter/sec",
            "range": "stddev: 3.1769260188594844e-7",
            "extra": "mean: 2.843239800043307 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 717636.1524311183,
            "unit": "iter/sec",
            "range": "stddev: 1.4885248358749347e-7",
            "extra": "mean: 1.3934638000222321 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 312622.46008053154,
            "unit": "iter/sec",
            "range": "stddev: 1.735227780939083e-7",
            "extra": "mean: 3.1987464999872373 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 15658.924395051568,
            "unit": "iter/sec",
            "range": "stddev: 0.0002939386943402743",
            "extra": "mean: 63.8613467165097 usec\nrounds: 4782"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8310.938418061045,
            "unit": "iter/sec",
            "range": "stddev: 0.000016047993827312035",
            "extra": "mean: 120.32335576291054 usec\nrounds: 5900"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6485.841564013228,
            "unit": "iter/sec",
            "range": "stddev: 0.000019469190627537626",
            "extra": "mean: 154.1819962961341 usec\nrounds: 4860"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3133.617740604084,
            "unit": "iter/sec",
            "range": "stddev: 0.000015643876297991275",
            "extra": "mean: 319.1199702000745 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3170.109181533668,
            "unit": "iter/sec",
            "range": "stddev: 0.000015208756615128093",
            "extra": "mean: 315.4465486000106 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4931.392850104239,
            "unit": "iter/sec",
            "range": "stddev: 0.000012212831583187362",
            "extra": "mean: 202.78246539998577 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 5029.62211030425,
            "unit": "iter/sec",
            "range": "stddev: 0.000012102773841951452",
            "extra": "mean: 198.8220940001213 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 89922.48381553034,
            "unit": "iter/sec",
            "range": "stddev: 5.280531915932418e-7",
            "extra": "mean: 11.1206892600012 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19442.136768666718,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020940488977320864",
            "extra": "mean: 51.43467571998656 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15376.8510069362,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017353059936974645",
            "extra": "mean: 65.03282105997641 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11638.174176706745,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022855054820188708",
            "extra": "mean: 85.92413078001982 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13091.261305438584,
            "unit": "iter/sec",
            "range": "stddev: 0.000002034153785332854",
            "extra": "mean: 76.38683368000329 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13602.38308049386,
            "unit": "iter/sec",
            "range": "stddev: 0.000005305448043461661",
            "extra": "mean: 73.51652972000352 usec\nrounds: 5000"
          }
        ]
      },
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
          "id": "a8acadfa5ccfaa0340d76624fde88b0f3b858bc5",
          "message": "Merge pull request #216 from evo-company/query-merger-edge-case\n\nFix query merger fragment type handling for nested abstract selections",
          "timestamp": "2026-04-01T12:35:04+03:00",
          "tree_id": "9f3bd49d78dbe4476b957c59696676c9321ca28c",
          "url": "https://github.com/evo-company/hiku/commit/a8acadfa5ccfaa0340d76624fde88b0f3b858bc5"
        },
        "date": 1775036251029,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64536.15622536596,
            "unit": "iter/sec",
            "range": "stddev: 0.000001654359499616957",
            "extra": "mean: 15.495189959995626 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1348.3813300130032,
            "unit": "iter/sec",
            "range": "stddev: 0.000035225594900905456",
            "extra": "mean: 741.6299660500019 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1365.6931252934903,
            "unit": "iter/sec",
            "range": "stddev: 0.00002400284911548745",
            "extra": "mean: 732.2289184000234 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1375.6666159976328,
            "unit": "iter/sec",
            "range": "stddev: 0.000006975021024256339",
            "extra": "mean: 726.9203078500241 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.07201978520055,
            "unit": "iter/sec",
            "range": "stddev: 0.0005694126641409787",
            "extra": "mean: 7.62939337959993 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3290.93350117471,
            "unit": "iter/sec",
            "range": "stddev: 0.000017736374512989598",
            "extra": "mean: 303.86514940002485 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1971.3709195873278,
            "unit": "iter/sec",
            "range": "stddev: 0.00001666724092570431",
            "extra": "mean: 507.26121099997385 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 462.4949371002988,
            "unit": "iter/sec",
            "range": "stddev: 0.0005750936622077991",
            "extra": "mean: 2.1621858311999973 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1480.168911547703,
            "unit": "iter/sec",
            "range": "stddev: 0.00002266694991966473",
            "extra": "mean: 675.5985699999428 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 589.6304908263049,
            "unit": "iter/sec",
            "range": "stddev: 0.00024798665093368223",
            "extra": "mean: 1.6959774223999262 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 431.9686502670762,
            "unit": "iter/sec",
            "range": "stddev: 0.0005739203487617167",
            "extra": "mean: 2.3149828104000676 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 363.7263098462,
            "unit": "iter/sec",
            "range": "stddev: 0.00048118644742439895",
            "extra": "mean: 2.7493199499998924 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 61.49572459584048,
            "unit": "iter/sec",
            "range": "stddev: 0.003930716258569295",
            "extra": "mean: 16.261293066666934 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 353287.393960831,
            "unit": "iter/sec",
            "range": "stddev: 2.402162744561738e-7",
            "extra": "mean: 2.830556699996123 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 727976.8794568067,
            "unit": "iter/sec",
            "range": "stddev: 1.416529862721852e-7",
            "extra": "mean: 1.3736699999952862 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 317092.9929066738,
            "unit": "iter/sec",
            "range": "stddev: 1.9104459184369053e-7",
            "extra": "mean: 3.1536490000405593 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 15758.332997361713,
            "unit": "iter/sec",
            "range": "stddev: 0.00038454520302973747",
            "extra": "mean: 63.458488925663765 usec\nrounds: 4831"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8405.190592010991,
            "unit": "iter/sec",
            "range": "stddev: 0.000020930741340253557",
            "extra": "mean: 118.97410166409375 usec\nrounds: 6069"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6646.302371470918,
            "unit": "iter/sec",
            "range": "stddev: 0.000021858323551993286",
            "extra": "mean: 150.45960055812 usec\nrounds: 5017"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3083.9934973504314,
            "unit": "iter/sec",
            "range": "stddev: 0.000016046774331548224",
            "extra": "mean: 324.2548989999932 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3113.6365343768653,
            "unit": "iter/sec",
            "range": "stddev: 0.000016291611028388524",
            "extra": "mean: 321.16786560000037 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4761.721689581484,
            "unit": "iter/sec",
            "range": "stddev: 0.000013917848948796167",
            "extra": "mean: 210.0080737998553 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4946.622172488299,
            "unit": "iter/sec",
            "range": "stddev: 0.000015183554712377859",
            "extra": "mean: 202.15815259991246 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 90569.82704048895,
            "unit": "iter/sec",
            "range": "stddev: 5.877501177929143e-7",
            "extra": "mean: 11.041204700026128 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19804.01416830899,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033099425943059394",
            "extra": "mean: 50.49481340001421 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 16042.231299660423,
            "unit": "iter/sec",
            "range": "stddev: 0.000008014754617868635",
            "extra": "mean: 62.33546826002737 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 12344.163487390422,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032551113611826305",
            "extra": "mean: 81.00994458000343 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13406.611152820844,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022557237450944098",
            "extra": "mean: 74.59006520000344 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13552.704065656704,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027971140181028113",
            "extra": "mean: 73.7860131199983 usec\nrounds: 5000"
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
          "id": "cbdcb528f78488647fd83bff76ca2226f4a450d6",
          "message": "update uv.lock",
          "timestamp": "2026-04-01T12:43:35+03:00",
          "tree_id": "e2ddb1a28e2657a6dd9fb79c7dd645c4b84d583c",
          "url": "https://github.com/evo-company/hiku/commit/cbdcb528f78488647fd83bff76ca2226f4a450d6"
        },
        "date": 1775036763597,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64105.54977745978,
            "unit": "iter/sec",
            "range": "stddev: 0.000001551797390002287",
            "extra": "mean: 15.599273439998028 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1347.028326516895,
            "unit": "iter/sec",
            "range": "stddev: 0.00003945448738779884",
            "extra": "mean: 742.3748857500048 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1370.4020154323339,
            "unit": "iter/sec",
            "range": "stddev: 0.000025032372326265356",
            "extra": "mean: 729.7128789499922 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1362.9546384762602,
            "unit": "iter/sec",
            "range": "stddev: 0.000009028598335803538",
            "extra": "mean: 733.7001333499757 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.28423982970156,
            "unit": "iter/sec",
            "range": "stddev: 0.00044160748703379616",
            "extra": "mean: 7.61706051919997 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3268.391761751391,
            "unit": "iter/sec",
            "range": "stddev: 0.000016937680540083356",
            "extra": "mean: 305.9608740000442 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1955.642351726474,
            "unit": "iter/sec",
            "range": "stddev: 0.00002369667041090223",
            "extra": "mean: 511.3409407999285 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 458.5464131491233,
            "unit": "iter/sec",
            "range": "stddev: 0.0005184706881586736",
            "extra": "mean: 2.180804322799906 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1465.6365894049675,
            "unit": "iter/sec",
            "range": "stddev: 0.00001785087255456924",
            "extra": "mean: 682.2973766000132 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 585.7132351153916,
            "unit": "iter/sec",
            "range": "stddev: 0.00023487153434058967",
            "extra": "mean: 1.7073201356001277 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 436.17927133522034,
            "unit": "iter/sec",
            "range": "stddev: 0.0003990200056478333",
            "extra": "mean: 2.2926353123999377 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 365.9620244085324,
            "unit": "iter/sec",
            "range": "stddev: 0.0003915274905871213",
            "extra": "mean: 2.732523959599905 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 65.03045038917051,
            "unit": "iter/sec",
            "range": "stddev: 0.0025568891620788214",
            "extra": "mean: 15.377411566667073 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 344406.0450893205,
            "unit": "iter/sec",
            "range": "stddev: 3.5852089995343123e-7",
            "extra": "mean: 2.9035494999533284 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 725349.3645226163,
            "unit": "iter/sec",
            "range": "stddev: 1.7461392241528547e-7",
            "extra": "mean: 1.3786459999977296 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 316314.645894984,
            "unit": "iter/sec",
            "range": "stddev: 1.839559847424482e-7",
            "extra": "mean: 3.161409100013657 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 15914.513110217124,
            "unit": "iter/sec",
            "range": "stddev: 0.0003054678632878438",
            "extra": "mean: 62.83572692889987 usec\nrounds: 5288"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8443.8326368764,
            "unit": "iter/sec",
            "range": "stddev: 0.00001666361131699917",
            "extra": "mean: 118.42963296462575 usec\nrounds: 6152"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6643.622533936621,
            "unit": "iter/sec",
            "range": "stddev: 0.000020631388657793465",
            "extra": "mean: 150.520291436163 usec\nrounds: 5068"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3082.401975301154,
            "unit": "iter/sec",
            "range": "stddev: 0.000015794229654039405",
            "extra": "mean: 324.4223200000704 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3128.215647319451,
            "unit": "iter/sec",
            "range": "stddev: 0.000015397595916930878",
            "extra": "mean: 319.6710562000078 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4847.32177328414,
            "unit": "iter/sec",
            "range": "stddev: 0.000012244224828666867",
            "extra": "mean: 206.2994880000474 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4960.7376810607475,
            "unit": "iter/sec",
            "range": "stddev: 0.000012791164758046885",
            "extra": "mean: 201.5829225999653 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 86925.90945740475,
            "unit": "iter/sec",
            "range": "stddev: 6.735706520702612e-7",
            "extra": "mean: 11.504049899990036 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19013.09585043493,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016432663939695386",
            "extra": "mean: 52.59532733997787 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15132.587421221708,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017320224972929803",
            "extra": "mean: 66.08255232000943 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11571.774805280242,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019744553404814337",
            "extra": "mean: 86.41716735998841 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13015.916110046895,
            "unit": "iter/sec",
            "range": "stddev: 0.000004389712827769031",
            "extra": "mean: 76.82901391997348 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13467.28312228863,
            "unit": "iter/sec",
            "range": "stddev: 0.000004105862914722929",
            "extra": "mean: 74.25402665998604 usec\nrounds: 5000"
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
          "id": "7f4a350a3e69770a031529c9aa832918d3bb77a0",
          "message": "update changelog for 0.8.0rc24",
          "timestamp": "2026-04-01T12:57:01+03:00",
          "tree_id": "04fc3a8f5aff1fa5eccb5748c8057a16be668b8c",
          "url": "https://github.com/evo-company/hiku/commit/7f4a350a3e69770a031529c9aa832918d3bb77a0"
        },
        "date": 1775037570013,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 63822.21666986492,
            "unit": "iter/sec",
            "range": "stddev: 8.552630292770853e-7",
            "extra": "mean: 15.668525039998684 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1366.6645022390899,
            "unit": "iter/sec",
            "range": "stddev: 0.000042767163486225926",
            "extra": "mean: 731.7084759000026 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1357.862227241271,
            "unit": "iter/sec",
            "range": "stddev: 0.000014793423693717535",
            "extra": "mean: 736.4517400499981 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1357.1796156062842,
            "unit": "iter/sec",
            "range": "stddev: 0.000021237281364755696",
            "extra": "mean: 736.822148300007 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.6672594891102,
            "unit": "iter/sec",
            "range": "stddev: 0.00048665469285064783",
            "extra": "mean: 7.594902513200003 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3353.0293024040916,
            "unit": "iter/sec",
            "range": "stddev: 0.000015107850856644973",
            "extra": "mean: 298.23777539999696 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1989.161923951182,
            "unit": "iter/sec",
            "range": "stddev: 0.000015251989676608924",
            "extra": "mean: 502.7242819999515 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 471.66808975373544,
            "unit": "iter/sec",
            "range": "stddev: 0.00040015675131955386",
            "extra": "mean: 2.120134946000087 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1482.636260518823,
            "unit": "iter/sec",
            "range": "stddev: 0.000040978436749159245",
            "extra": "mean: 674.4742635999387 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 590.899959850206,
            "unit": "iter/sec",
            "range": "stddev: 0.0002300679283357704",
            "extra": "mean: 1.6923338431999584 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 440.0364971551388,
            "unit": "iter/sec",
            "range": "stddev: 0.000405793153378606",
            "extra": "mean: 2.272538769999892 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 368.440487882851,
            "unit": "iter/sec",
            "range": "stddev: 0.0003843994462928976",
            "extra": "mean: 2.7141425355998305 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 65.24962644964064,
            "unit": "iter/sec",
            "range": "stddev: 0.0024551361048904237",
            "extra": "mean: 15.325758236666616 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 345924.95559784566,
            "unit": "iter/sec",
            "range": "stddev: 3.344162181362385e-7",
            "extra": "mean: 2.8908003999646326 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 718267.6877285664,
            "unit": "iter/sec",
            "range": "stddev: 1.6217959026821262e-7",
            "extra": "mean: 1.3922386000160714 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 311613.2460790761,
            "unit": "iter/sec",
            "range": "stddev: 2.0983657557087791e-7",
            "extra": "mean: 3.209106200017686 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 16247.954771953955,
            "unit": "iter/sec",
            "range": "stddev: 0.0002897790674633052",
            "extra": "mean: 61.54620775570645 usec\nrounds: 4977"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8487.573349414717,
            "unit": "iter/sec",
            "range": "stddev: 0.000015795745692853942",
            "extra": "mean: 117.81930580534632 usec\nrounds: 6115"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6749.421259575295,
            "unit": "iter/sec",
            "range": "stddev: 0.000018951740704660234",
            "extra": "mean: 148.16085135911706 usec\nrounds: 5039"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3144.739197748054,
            "unit": "iter/sec",
            "range": "stddev: 0.000015235796460871216",
            "extra": "mean: 317.991393599857 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3166.981234045183,
            "unit": "iter/sec",
            "range": "stddev: 0.000015481058909033694",
            "extra": "mean: 315.7581071999914 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4891.458788727599,
            "unit": "iter/sec",
            "range": "stddev: 0.00001232667975363027",
            "extra": "mean: 204.4379893999121 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 5037.455867086197,
            "unit": "iter/sec",
            "range": "stddev: 0.000012398869126700589",
            "extra": "mean: 198.5129054000879 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 90387.09459156157,
            "unit": "iter/sec",
            "range": "stddev: 6.054812032046308e-7",
            "extra": "mean: 11.063526319977086 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19340.91041917074,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011498754397674217",
            "extra": "mean: 51.703874240004666 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15537.320019015968,
            "unit": "iter/sec",
            "range": "stddev: 0.000001422522811504249",
            "extra": "mean: 64.36116388000698 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11893.535984103448,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015417449890708133",
            "extra": "mean: 84.07928485999207 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13359.025860731197,
            "unit": "iter/sec",
            "range": "stddev: 0.000004368010932643943",
            "extra": "mean: 74.85575748000429 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13543.383849233764,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016589002491362176",
            "extra": "mean: 73.83679080000206 usec\nrounds: 5000"
          }
        ]
      },
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
          "id": "9a1862379998a6e3de16e2e7a6e79b3384b7f9ad",
          "message": "Merge pull request #217 from evo-company/fix-root-fragment\n\nFix root fragment not being processed",
          "timestamp": "2026-05-25T17:43:35+03:00",
          "tree_id": "46215370973a11cc4c10b158a79e1ced705be846",
          "url": "https://github.com/evo-company/hiku/commit/9a1862379998a6e3de16e2e7a6e79b3384b7f9ad"
        },
        "date": 1779720354063,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64993.365165331124,
            "unit": "iter/sec",
            "range": "stddev: 5.50535573223218e-7",
            "extra": "mean: 15.386185919996366 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1391.5424849357892,
            "unit": "iter/sec",
            "range": "stddev: 0.000019123104761593822",
            "extra": "mean: 718.6269990500101 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1373.9343985836708,
            "unit": "iter/sec",
            "range": "stddev: 0.00003168868831731728",
            "extra": "mean: 727.8367882999775 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1389.2858563867017,
            "unit": "iter/sec",
            "range": "stddev: 0.000013839708576254696",
            "extra": "mean: 719.7942708499397 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.51373886974338,
            "unit": "iter/sec",
            "range": "stddev: 0.0004683762092756572",
            "extra": "mean: 7.603768310400187 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3843.0856507313133,
            "unit": "iter/sec",
            "range": "stddev: 0.000016787787155017787",
            "extra": "mean: 260.2075756000147 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2209.2661458687367,
            "unit": "iter/sec",
            "range": "stddev: 0.000020148400452448576",
            "extra": "mean: 452.63899139991395 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 484.330201983859,
            "unit": "iter/sec",
            "range": "stddev: 0.00041078250087654765",
            "extra": "mean: 2.064707086000237 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1629.1801077989637,
            "unit": "iter/sec",
            "range": "stddev: 0.00002358272218744794",
            "extra": "mean: 613.8056776000099 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 615.5877751094904,
            "unit": "iter/sec",
            "range": "stddev: 0.00022608100542855384",
            "extra": "mean: 1.6244637083998896 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 455.6664354007572,
            "unit": "iter/sec",
            "range": "stddev: 0.0003866303990700225",
            "extra": "mean: 2.194587800000022 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 371.8042293599175,
            "unit": "iter/sec",
            "range": "stddev: 0.0004565558274341425",
            "extra": "mean: 2.689587479199895 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 64.16548642381983,
            "unit": "iter/sec",
            "range": "stddev: 0.0029168378458032254",
            "extra": "mean: 15.584702240000087 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 381622.0440480669,
            "unit": "iter/sec",
            "range": "stddev: 1.851055356186439e-7",
            "extra": "mean: 2.620393699987744 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 795924.0411553802,
            "unit": "iter/sec",
            "range": "stddev: 2.5534702571136715e-7",
            "extra": "mean: 1.2564012999888519 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 336548.7537833672,
            "unit": "iter/sec",
            "range": "stddev: 1.8144857360587506e-7",
            "extra": "mean: 2.9713376999865204 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 19677.178757868933,
            "unit": "iter/sec",
            "range": "stddev: 0.0002981554564935023",
            "extra": "mean: 50.82029351388083 usec\nrounds: 4579"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 10240.484826778107,
            "unit": "iter/sec",
            "range": "stddev: 0.000014193784970893615",
            "extra": "mean: 97.65162655044166 usec\nrounds: 5966"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 8029.92849844379,
            "unit": "iter/sec",
            "range": "stddev: 0.00001734545446200592",
            "extra": "mean: 124.53411013482886 usec\nrounds: 5121"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3608.205583118576,
            "unit": "iter/sec",
            "range": "stddev: 0.000018562475197233735",
            "extra": "mean: 277.1460708000177 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3635.6816221542585,
            "unit": "iter/sec",
            "range": "stddev: 0.000016788567493399765",
            "extra": "mean: 275.0515869999276 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 5937.032472422471,
            "unit": "iter/sec",
            "range": "stddev: 0.000013799894443343221",
            "extra": "mean: 168.43431539999187 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 6142.83285970675,
            "unit": "iter/sec",
            "range": "stddev: 0.000013085327281870971",
            "extra": "mean: 162.7913412001476 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 88406.54247884963,
            "unit": "iter/sec",
            "range": "stddev: 4.6128130402607425e-7",
            "extra": "mean: 11.3113800399924 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19347.830114238204,
            "unit": "iter/sec",
            "range": "stddev: 9.94280674770767e-7",
            "extra": "mean: 51.68538250002996 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15574.62581476912,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011076449959438038",
            "extra": "mean: 64.20700001997602 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11993.111090787355,
            "unit": "iter/sec",
            "range": "stddev: 0.000003845185993488288",
            "extra": "mean: 83.38120046000085 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13518.711476344632,
            "unit": "iter/sec",
            "range": "stddev: 0.000003061088055566824",
            "extra": "mean: 73.97154690000036 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 14212.135966600235,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029086945157778053",
            "extra": "mean: 70.36240030000329 usec\nrounds: 5000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "slavikovbasa@gmail.com",
            "name": "skovbasa",
            "username": "skovbasa"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "235fe35baabd7855ed2c8cb6e5189f3cabed5e74",
          "message": "Merge pull request #219 from evo-company/upd-query-aliases-validator\n\nUpd query aliases validator to count only the same field repetitions.…",
          "timestamp": "2026-06-23T12:33:04+03:00",
          "tree_id": "37374641de47f1a02514af705e31745de1383b47",
          "url": "https://github.com/evo-company/hiku/commit/235fe35baabd7855ed2c8cb6e5189f3cabed5e74"
        },
        "date": 1782207324732,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64878.09430087648,
            "unit": "iter/sec",
            "range": "stddev: 5.036271374237164e-7",
            "extra": "mean: 15.413523019995525 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1349.4688251982766,
            "unit": "iter/sec",
            "range": "stddev: 0.000028538387044533796",
            "extra": "mean: 741.032309400012 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1373.990764092567,
            "unit": "iter/sec",
            "range": "stddev: 0.000016069082463512813",
            "extra": "mean: 727.8069301000257 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1382.2373399234493,
            "unit": "iter/sec",
            "range": "stddev: 0.000011409163986317844",
            "extra": "mean: 723.4647560999775 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 134.16814139099844,
            "unit": "iter/sec",
            "range": "stddev: 0.0005192149698303208",
            "extra": "mean: 7.4533342240000025 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3859.3592822157607,
            "unit": "iter/sec",
            "range": "stddev: 0.000016975401518510727",
            "extra": "mean: 259.1103670000564 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2204.242288411281,
            "unit": "iter/sec",
            "range": "stddev: 0.00003304093492366368",
            "extra": "mean: 453.6706356000252 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 482.2683101530106,
            "unit": "iter/sec",
            "range": "stddev: 0.0005098477580658302",
            "extra": "mean: 2.073534542799894 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1630.0238303911394,
            "unit": "iter/sec",
            "range": "stddev: 0.00001828353938199339",
            "extra": "mean: 613.4879633999219 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 616.3376945074954,
            "unit": "iter/sec",
            "range": "stddev: 0.00027032641726132086",
            "extra": "mean: 1.6224871671999268 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 457.0804051866765,
            "unit": "iter/sec",
            "range": "stddev: 0.0004118930040959826",
            "extra": "mean: 2.1877988831999686 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 381.6255830772127,
            "unit": "iter/sec",
            "range": "stddev: 0.0005542051801156627",
            "extra": "mean: 2.6203693995999062 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 63.748455015555365,
            "unit": "iter/sec",
            "range": "stddev: 0.003121842272569383",
            "extra": "mean: 15.6866546766661 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 382451.32790069055,
            "unit": "iter/sec",
            "range": "stddev: 2.70354561165922e-7",
            "extra": "mean: 2.61471180003241 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 819205.7882222026,
            "unit": "iter/sec",
            "range": "stddev: 1.1822407389399016e-7",
            "extra": "mean: 1.2206944999377356 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 333968.1399760039,
            "unit": "iter/sec",
            "range": "stddev: 2.2118037945092648e-7",
            "extra": "mean: 2.9942975999802 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 21957.334974715497,
            "unit": "iter/sec",
            "range": "stddev: 0.000010710695040697104",
            "extra": "mean: 45.542867618111615 usec\nrounds: 4555"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 10459.301685909713,
            "unit": "iter/sec",
            "range": "stddev: 0.000013730948682479837",
            "extra": "mean: 95.60867733140863 usec\nrounds: 5845"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 8132.045018939722,
            "unit": "iter/sec",
            "range": "stddev: 0.000017503676454260582",
            "extra": "mean: 122.97029808258276 usec\nrounds: 5059"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3548.9765593420434,
            "unit": "iter/sec",
            "range": "stddev: 0.00018292678197955192",
            "extra": "mean: 281.77137359999733 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3666.723558080817,
            "unit": "iter/sec",
            "range": "stddev: 0.000016245898078732784",
            "extra": "mean: 272.7230412001404 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 5899.925034956429,
            "unit": "iter/sec",
            "range": "stddev: 0.000013420708644049225",
            "extra": "mean: 169.49367900017478 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 6059.096111821345,
            "unit": "iter/sec",
            "range": "stddev: 0.000013578887043279524",
            "extra": "mean: 165.04111860001558 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 87938.26003867858,
            "unit": "iter/sec",
            "range": "stddev: 4.298379215127957e-7",
            "extra": "mean: 11.371614580049254 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19236.793624839785,
            "unit": "iter/sec",
            "range": "stddev: 9.37076880921201e-7",
            "extra": "mean: 51.98371513996676 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15534.724091906579,
            "unit": "iter/sec",
            "range": "stddev: 9.819879161976614e-7",
            "extra": "mean: 64.37191894003377 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11815.770749358267,
            "unit": "iter/sec",
            "range": "stddev: 0.000001975049709071639",
            "extra": "mean: 84.63265082003318 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13585.20768096863,
            "unit": "iter/sec",
            "range": "stddev: 9.445402148909445e-7",
            "extra": "mean: 73.60947462002287 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13911.373784363373,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010099969073797646",
            "extra": "mean: 71.88362670004722 usec\nrounds: 5000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "committer": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "distinct": true,
          "id": "fd812cf91a91989abba18c47c58e30547205b09a",
          "message": "Upd uv.lock version to rc27",
          "timestamp": "2026-06-23T12:35:26+03:00",
          "tree_id": "8ac738dbf77a504dc3b63a3aa36a74538011047f",
          "url": "https://github.com/evo-company/hiku/commit/fd812cf91a91989abba18c47c58e30547205b09a"
        },
        "date": 1782207472305,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 63907.396730985616,
            "unit": "iter/sec",
            "range": "stddev: 7.664159945320416e-7",
            "extra": "mean: 15.647640979798327 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1367.8267427681103,
            "unit": "iter/sec",
            "range": "stddev: 0.000026242292957174145",
            "extra": "mean: 731.086744199979 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1365.7474751212733,
            "unit": "iter/sec",
            "range": "stddev: 0.000018013870262549282",
            "extra": "mean: 732.1997794000708 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1369.5706928112318,
            "unit": "iter/sec",
            "range": "stddev: 0.000017147975530216896",
            "extra": "mean: 730.1558110500764 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 132.57188862588313,
            "unit": "iter/sec",
            "range": "stddev: 0.0004907065920175689",
            "extra": "mean: 7.543077271999891 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3859.6578656797114,
            "unit": "iter/sec",
            "range": "stddev: 0.00001780532437369859",
            "extra": "mean: 259.0903221998133 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2251.009014904669,
            "unit": "iter/sec",
            "range": "stddev: 0.000016635686137382096",
            "extra": "mean: 444.2452221997655 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 489.095363083304,
            "unit": "iter/sec",
            "range": "stddev: 0.000391560369037624",
            "extra": "mean: 2.0445910459995047 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1632.850275947173,
            "unit": "iter/sec",
            "range": "stddev: 0.00003156807567901106",
            "extra": "mean: 612.4260226002207 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 618.0057078866389,
            "unit": "iter/sec",
            "range": "stddev: 0.00021704726778834532",
            "extra": "mean: 1.6181080323993229 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 456.56485918010617,
            "unit": "iter/sec",
            "range": "stddev: 0.00038683573037340507",
            "extra": "mean: 2.190269312000464 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 380.23558400557675,
            "unit": "iter/sec",
            "range": "stddev: 0.0005252200648142623",
            "extra": "mean: 2.629948490000697 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 63.725033975854075,
            "unit": "iter/sec",
            "range": "stddev: 0.003115696457550085",
            "extra": "mean: 15.692420036667349 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 386551.2481471169,
            "unit": "iter/sec",
            "range": "stddev: 2.112772697740263e-7",
            "extra": "mean: 2.586979099908149 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 807302.4055206638,
            "unit": "iter/sec",
            "range": "stddev: 1.587624459492519e-7",
            "extra": "mean: 1.238693199923091 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 331889.6465389241,
            "unit": "iter/sec",
            "range": "stddev: 6.34926428143214e-7",
            "extra": "mean: 3.0130497001891854 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 21809.42918905758,
            "unit": "iter/sec",
            "range": "stddev: 0.000010651598229444142",
            "extra": "mean: 45.85172731167714 usec\nrounds: 4639"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 10450.031577008931,
            "unit": "iter/sec",
            "range": "stddev: 0.000014822007985866942",
            "extra": "mean: 95.69349074505149 usec\nrounds: 5997"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 8171.637091479344,
            "unit": "iter/sec",
            "range": "stddev: 0.000017796050217289776",
            "extra": "mean: 122.37449960213125 usec\nrounds: 5032"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3532.9669194886997,
            "unit": "iter/sec",
            "range": "stddev: 0.00013977843507847066",
            "extra": "mean: 283.048220600017 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3638.7841158516353,
            "unit": "iter/sec",
            "range": "stddev: 0.00001714012684378167",
            "extra": "mean: 274.8170730007587 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 5954.517879992154,
            "unit": "iter/sec",
            "range": "stddev: 0.00001363408564462117",
            "extra": "mean: 167.93970899980195 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 6139.0023258039655,
            "unit": "iter/sec",
            "range": "stddev: 0.000013442778395542663",
            "extra": "mean: 162.89291759944717 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 88171.72966573673,
            "unit": "iter/sec",
            "range": "stddev: 4.906363517766073e-7",
            "extra": "mean: 11.341503719968387 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 18999.67396023304,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029197064960623603",
            "extra": "mean: 52.63248212011604 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15288.858292043604,
            "unit": "iter/sec",
            "range": "stddev: 0.0000047823586288654606",
            "extra": "mean: 65.40710763997367 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 11798.70246095392,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016455182050831465",
            "extra": "mean: 84.75508246007166 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13343.896098161635,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017273449777541259",
            "extra": "mean: 74.94063148001942 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13547.460626850605,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014456896696491623",
            "extra": "mean: 73.81457141997771 usec\nrounds: 5000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "slavikovbasa@gmail.com",
            "name": "skovbasa",
            "username": "skovbasa"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "93e774ca4ce3674d447d042520a2756ea0ab5b6b",
          "message": "Merge pull request #220 from evo-company/one-more-alias-validation-upd\n\nFix alias validation for fragment alias collisions",
          "timestamp": "2026-06-23T13:28:02+03:00",
          "tree_id": "8f0fb1627e6c7b7a64ccc8504343b049b69eac93",
          "url": "https://github.com/evo-company/hiku/commit/93e774ca4ce3674d447d042520a2756ea0ab5b6b"
        },
        "date": 1782210629675,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 63850.24993494884,
            "unit": "iter/sec",
            "range": "stddev: 7.125952382135947e-7",
            "extra": "mean: 15.66164582000553 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1349.1771361698093,
            "unit": "iter/sec",
            "range": "stddev: 0.000023018223160291867",
            "extra": "mean: 741.1925189000079 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1362.725013409731,
            "unit": "iter/sec",
            "range": "stddev: 0.00003398859261200086",
            "extra": "mean: 733.8237649999968 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1343.0780947393087,
            "unit": "iter/sec",
            "range": "stddev: 0.000015822247758385516",
            "extra": "mean: 744.5583424499972 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 129.83213874040808,
            "unit": "iter/sec",
            "range": "stddev: 0.0005404486260616794",
            "extra": "mean: 7.702253153199939 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3221.4052825039835,
            "unit": "iter/sec",
            "range": "stddev: 0.00003216656998548741",
            "extra": "mean: 310.4235302000575 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 1958.8860110654173,
            "unit": "iter/sec",
            "range": "stddev: 0.00001588612923974967",
            "extra": "mean: 510.4942270000237 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 462.4646790242975,
            "unit": "iter/sec",
            "range": "stddev: 0.00039848547964499914",
            "extra": "mean: 2.16232729839993 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1467.1563442987112,
            "unit": "iter/sec",
            "range": "stddev: 0.000019043591444479723",
            "extra": "mean: 681.5906183999715 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 584.4173855444659,
            "unit": "iter/sec",
            "range": "stddev: 0.00021506920419708524",
            "extra": "mean: 1.711105837599888 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 433.1402317081471,
            "unit": "iter/sec",
            "range": "stddev: 0.0003777499281038215",
            "extra": "mean: 2.3087211179999714 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 360.67754151609074,
            "unit": "iter/sec",
            "range": "stddev: 0.0005252343305943036",
            "extra": "mean: 2.7725596548000966 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 64.38718401741575,
            "unit": "iter/sec",
            "range": "stddev: 0.0025522938928151193",
            "extra": "mean: 15.531041079999946 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 349891.2485539454,
            "unit": "iter/sec",
            "range": "stddev: 2.781688771765013e-7",
            "extra": "mean: 2.8580308999806903 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 720939.9903960882,
            "unit": "iter/sec",
            "range": "stddev: 1.58902109469187e-7",
            "extra": "mean: 1.3870780000019067 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 309097.32145408064,
            "unit": "iter/sec",
            "range": "stddev: 4.400658254466565e-7",
            "extra": "mean: 3.2352270000131966 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 16965.89849040794,
            "unit": "iter/sec",
            "range": "stddev: 0.000011363726298870634",
            "extra": "mean: 58.94176489181359 usec\nrounds: 5053"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 8406.266206064458,
            "unit": "iter/sec",
            "range": "stddev: 0.000016216485358862624",
            "extra": "mean: 118.95887847075066 usec\nrounds: 6015"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 6618.7304406213025,
            "unit": "iter/sec",
            "range": "stddev: 0.000022226425523783534",
            "extra": "mean: 151.08637660519827 usec\nrounds: 4984"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3018.5787533410526,
            "unit": "iter/sec",
            "range": "stddev: 0.00014963017599171097",
            "extra": "mean: 331.281732799971 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3108.771292877326,
            "unit": "iter/sec",
            "range": "stddev: 0.0000189967153180874",
            "extra": "mean: 321.670494800037 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 4792.527919878727,
            "unit": "iter/sec",
            "range": "stddev: 0.000012824133972624752",
            "extra": "mean: 208.65814799996087 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 4927.330808746045,
            "unit": "iter/sec",
            "range": "stddev: 0.000013232382183522663",
            "extra": "mean: 202.94963720012333 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 89459.48278134552,
            "unit": "iter/sec",
            "range": "stddev: 5.586030720904275e-7",
            "extra": "mean: 11.178244819994916 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19458.250715456572,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011346508584453684",
            "extra": "mean: 51.392081159980876 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15803.645854822487,
            "unit": "iter/sec",
            "range": "stddev: 0.000002018512611342481",
            "extra": "mean: 63.276538160012585 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 12013.429743908648,
            "unit": "iter/sec",
            "range": "stddev: 0.000002064993599514648",
            "extra": "mean: 83.24017548003269 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13213.275252274201,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013562269834769513",
            "extra": "mean: 75.6814628400241 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13393.72186785578,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021837436618324596",
            "extra": "mean: 74.66184603996794 usec\nrounds: 5000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "committer": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "distinct": true,
          "id": "1fb596936c277fbb406fc70e90274fb647c69dae",
          "message": "Upd changelog for 0.8.0rc28",
          "timestamp": "2026-06-23T13:29:49+03:00",
          "tree_id": "cf49b90f4c2f76eb3af2a75e1364d0c6c30dca71",
          "url": "https://github.com/evo-company/hiku/commit/1fb596936c277fbb406fc70e90274fb647c69dae"
        },
        "date": 1782210732608,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64403.26467923055,
            "unit": "iter/sec",
            "range": "stddev: 4.5757353983894004e-7",
            "extra": "mean: 15.527163180013304 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1391.331356979492,
            "unit": "iter/sec",
            "range": "stddev: 0.00001762543164917484",
            "extra": "mean: 718.7360473000105 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1392.19578991793,
            "unit": "iter/sec",
            "range": "stddev: 0.00001945473277121584",
            "extra": "mean: 718.2897745000006 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1375.4999973439387,
            "unit": "iter/sec",
            "range": "stddev: 0.000015477835575485957",
            "extra": "mean: 727.0083619999845 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 131.60446681136082,
            "unit": "iter/sec",
            "range": "stddev: 0.0007173800009574473",
            "extra": "mean: 7.598526282799957 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3814.2146862192353,
            "unit": "iter/sec",
            "range": "stddev: 0.000017522527101142182",
            "extra": "mean: 262.17716680002354 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2208.281848290494,
            "unit": "iter/sec",
            "range": "stddev: 0.00001857624156810147",
            "extra": "mean: 452.84074620009847 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 474.24183563818724,
            "unit": "iter/sec",
            "range": "stddev: 0.0005567899479807171",
            "extra": "mean: 2.1086288151999497 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1612.2261106027365,
            "unit": "iter/sec",
            "range": "stddev: 0.000018685719500724176",
            "extra": "mean: 620.260392400013 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 602.3990491046843,
            "unit": "iter/sec",
            "range": "stddev: 0.00024394241300544566",
            "extra": "mean: 1.6600291808000862 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 451.1704758516017,
            "unit": "iter/sec",
            "range": "stddev: 0.00044519755629207354",
            "extra": "mean: 2.2164570900000964 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 378.1507345060603,
            "unit": "iter/sec",
            "range": "stddev: 0.0004928254887631511",
            "extra": "mean: 2.64444812280002 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 64.33154183370019,
            "unit": "iter/sec",
            "range": "stddev: 0.0028801069360082617",
            "extra": "mean: 15.54447432000065 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 385053.5459319985,
            "unit": "iter/sec",
            "range": "stddev: 2.1535230996930177e-7",
            "extra": "mean: 2.597041399994282 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 815989.4770223409,
            "unit": "iter/sec",
            "range": "stddev: 1.2656730384113094e-7",
            "extra": "mean: 1.2255059999660034 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 303129.1690726943,
            "unit": "iter/sec",
            "range": "stddev: 2.171918800864561e-7",
            "extra": "mean: 3.298923699949796 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 21803.30465655256,
            "unit": "iter/sec",
            "range": "stddev: 0.000010568727200929718",
            "extra": "mean: 45.864607028708804 usec\nrounds: 5008"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 10127.519314974097,
            "unit": "iter/sec",
            "range": "stddev: 0.000023837590339752667",
            "extra": "mean: 98.74086327551554 usec\nrounds: 5544"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 8217.174359254057,
            "unit": "iter/sec",
            "range": "stddev: 0.000017869095604186956",
            "extra": "mean: 121.69633456466885 usec\nrounds: 5144"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3564.380497824988,
            "unit": "iter/sec",
            "range": "stddev: 0.000026983441253024088",
            "extra": "mean: 280.553661599879 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3612.976372588283,
            "unit": "iter/sec",
            "range": "stddev: 0.00012603740173074867",
            "extra": "mean: 276.7801105999524 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 5936.60327014361,
            "unit": "iter/sec",
            "range": "stddev: 0.000012982539521430724",
            "extra": "mean: 168.44649279988175 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 6075.768357796346,
            "unit": "iter/sec",
            "range": "stddev: 0.000015346534422897075",
            "extra": "mean: 164.58823660003645 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 91214.45884021133,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010653258659890007",
            "extra": "mean: 10.963174180003534 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 20077.202626331276,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010631392349408864",
            "extra": "mean: 49.8077356000033 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 16222.076300103714,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013415284727588703",
            "extra": "mean: 61.64439012000002 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 12478.531304574999,
            "unit": "iter/sec",
            "range": "stddev: 0.000001535275388187126",
            "extra": "mean: 80.13763604001781 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13557.121879377304,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012753944561149099",
            "extra": "mean: 73.7619687200106 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13940.248407846482,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013031694218267251",
            "extra": "mean: 71.73473318001527 usec\nrounds: 5000"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "committer": {
            "email": "slavikovbasa@gmail.com",
            "name": "s.kovbasa",
            "username": "skovbasa"
          },
          "distinct": true,
          "id": "e0a1aeeed1a355bc728a72d9dc9b0ef18f8473fb",
          "message": "release",
          "timestamp": "2026-06-23T13:30:24+03:00",
          "tree_id": "f02379dca86f0672f02a2d0bb43fe8ab9013ee0b",
          "url": "https://github.com/evo-company/hiku/commit/e0a1aeeed1a355bc728a72d9dc9b0ef18f8473fb"
        },
        "date": 1782210764728,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_shallow",
            "value": 64957.330114476936,
            "unit": "iter/sec",
            "range": "stddev: 6.612097068224902e-7",
            "extra": "mean: 15.394721399996884 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep",
            "value": 1385.3345589076034,
            "unit": "iter/sec",
            "range": "stddev: 0.000027370200662615102",
            "extra": "mean: 721.847292099999 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_inline_fragments",
            "value": 1384.3942734855843,
            "unit": "iter/sec",
            "range": "stddev: 0.0000216968785251134",
            "extra": "mean: 722.3375733000047 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_named_fragments",
            "value": 1390.698439719647,
            "unit": "iter/sec",
            "range": "stddev: 0.000014545579274447231",
            "extra": "mean: 719.0631494499926 usec\nrounds: 2000"
          },
          {
            "name": "tests/benchmarks/test_denormalize.py::test_denormalize_deep_large",
            "value": 133.95180072075735,
            "unit": "iter/sec",
            "range": "stddev: 0.0004765955710640394",
            "extra": "mean: 7.465371832400001 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_shallow",
            "value": 3779.8522372909442,
            "unit": "iter/sec",
            "range": "stddev: 0.00002930866837309481",
            "extra": "mean: 264.56060639997645 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_medium",
            "value": 2209.148723573398,
            "unit": "iter/sec",
            "range": "stddev: 0.000033071538624347234",
            "extra": "mean: 452.66305039999963 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep",
            "value": 487.2276762004174,
            "unit": "iter/sec",
            "range": "stddev: 0.00040605971596585877",
            "extra": "mean: 2.05242856440006 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_wide",
            "value": 1630.088737095138,
            "unit": "iter/sec",
            "range": "stddev: 0.00001881645036786572",
            "extra": "mean: 613.4635355999251 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_cached",
            "value": 616.7637260999205,
            "unit": "iter/sec",
            "range": "stddev: 0.0002068526747252689",
            "extra": "mean: 1.621366428799985 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_inline_fragments",
            "value": 457.5052801306593,
            "unit": "iter/sec",
            "range": "stddev: 0.00040114269851659033",
            "extra": "mean: 2.1857671231999976 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_engine_execute.py::test_engine_execute_deep_named_fragments",
            "value": 382.39965739951714,
            "unit": "iter/sec",
            "range": "stddev: 0.0005012821667073668",
            "extra": "mean: 2.61506510440002 msec\nrounds: 500"
          },
          {
            "name": "tests/benchmarks/test_graph_init.py::test_graph_init_speed",
            "value": 63.481400094719866,
            "unit": "iter/sec",
            "range": "stddev: 0.00289006810865412",
            "extra": "mean: 15.752645633333724 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_hashable",
            "value": 383625.51275567047,
            "unit": "iter/sec",
            "range": "stddev: 1.8255587530244702e-7",
            "extra": "mean: 2.6067087999877003 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_unhashable",
            "value": 813005.1556522393,
            "unit": "iter/sec",
            "range": "stddev: 1.251846839224432e-7",
            "extra": "mean: 1.2300045000301907 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_is_hashable.py::test_is_hashable_mixed_list",
            "value": 338033.886068376,
            "unit": "iter/sec",
            "range": "stddev: 1.790369452026673e-7",
            "extra": "mean: 2.958283300029052 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_field",
            "value": 21382.756338393738,
            "unit": "iter/sec",
            "range": "stddev: 0.000010296556684248558",
            "extra": "mean: 46.766655531890116 usec\nrounds: 4700"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link",
            "value": 10207.944721527305,
            "unit": "iter/sec",
            "range": "stddev: 0.000017653740493639966",
            "extra": "mean: 97.96291293497333 usec\nrounds: 6007"
          },
          {
            "name": "tests/benchmarks/test_read_graphql.py::test_link_fragment",
            "value": 8148.867799246148,
            "unit": "iter/sec",
            "range": "stddev: 0.000018000381400509293",
            "extra": "mean: 122.71643431158743 usec\nrounds: 5077"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_federated_schema",
            "value": 3651.1542711273896,
            "unit": "iter/sec",
            "range": "stddev: 0.00001873813823530931",
            "extra": "mean: 273.88598940006545 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema",
            "value": 3620.4698448377485,
            "unit": "iter/sec",
            "range": "stddev: 0.00013903077285763556",
            "extra": "mean: 276.2072445999934 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_parse_cache",
            "value": 6006.740415706959,
            "unit": "iter/sec",
            "range": "stddev: 0.00001320558478568376",
            "extra": "mean: 166.47964299990576 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_schema.py::test_schema_with_all_caches",
            "value": 6144.1856111080815,
            "unit": "iter/sec",
            "range": "stddev: 0.000013472526554554445",
            "extra": "mean: 162.7554998000221 usec\nrounds: 1000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_shallow",
            "value": 89063.39677956549,
            "unit": "iter/sec",
            "range": "stddev: 4.4062377798864407e-7",
            "extra": "mean: 11.227957119971848 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep",
            "value": 19257.04712323936,
            "unit": "iter/sec",
            "range": "stddev: 9.349756040305001e-7",
            "extra": "mean: 51.92904153997745 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_inline_fragments",
            "value": 15584.606929387084,
            "unit": "iter/sec",
            "range": "stddev: 8.390455356768826e-7",
            "extra": "mean: 64.16587883999512 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_deep_named_fragments",
            "value": 12006.116231604688,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016223090901398935",
            "extra": "mean: 83.29088114003241 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_shallow",
            "value": 13539.532366995236,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011203366948728158",
            "extra": "mean: 73.85779455999966 usec\nrounds: 5000"
          },
          {
            "name": "tests/benchmarks/test_validate.py::test_validate_wide_graph_deep",
            "value": 13836.618946892373,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012201492226044194",
            "extra": "mean: 72.27199099998302 usec\nrounds: 5000"
          }
        ]
      }
    ]
  }
}