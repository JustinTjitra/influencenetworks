"""Load data/processed into the graph, report invalid edges and basic stats.

Run:  python -m influence.validate
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .graph import build_graph, linked_entities, load_doc_registry, load_edges, load_nodes

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"


def main() -> int:
    nodes = load_nodes(PROC / "nodes.csv")
    docs = load_doc_registry(ROOT / "data" / "raw" / "documents.csv")
    edges, errors = load_edges(PROC / "edges.csv", nodes, doc_ids=docs)
    g = build_graph(nodes, edges)

    print(f"nodes: {g.number_of_nodes()}  valid edges: {len(edges)}  rejected: {len(errors)}")
    for e in errors:
        print("  REJECTED", e)
    print("edge types:", dict(Counter(e.type.value for e in edges)))
    print("confidence:", dict(Counter(e.confidence.value for e in edges)))
    isolated = [n for n in g.nodes if g.degree(n) == 0]
    print(f"isolated nodes ({len(isolated)}):", ", ".join(sorted(isolated)))

    # Owner networks for each outlet: the core input to the coverage analysis.
    print("\nowner network size per outlet (within 3 hops):")
    for n, d in g.nodes(data=True):
        if d["type"] == "outlet":
            net = linked_entities(g, n, max_hops=3)
            hits = sorted(k for k in net if g.nodes[k]["type"] in ("bank", "business_group", "party"))
            print(f"  {d['name']:<22} {len(net):>3} nodes; banks/groups/parties: {', '.join(hits) or '-'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
