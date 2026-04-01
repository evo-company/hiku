window.BENCHMARK_DATA = {
  "lastUpdate": 1775036251939,
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
      }
    ]
  }
}