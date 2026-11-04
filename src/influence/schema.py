"""Graph schema for the Indonesian political-business influence network.

Design rules (enforced by validate_edge):
  1. Every edge carries a source URL, a source type and a confidence level.
     An edge without a source does not enter the graph.
  2. Edge types describe documented relationships only. There is deliberately
     no edge type for allegations, suspicion or wrongdoing. Court outcomes are
     recorded only as CONVICTED_IN with a link to the verdict itself.
  3. Relationships are time-bound (start_date / end_date) so the media analysis
     can ask "was X linked to Y at the time this article was published?".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional
from urllib.parse import urlparse


class NodeType(str, Enum):
    PERSON = "person"
    BUSINESS_GROUP = "business_group"   # conglomerate / family group (informal)
    COMPANY = "company"                 # legal entity (PT, Tbk, Pte Ltd)
    BANK = "bank"
    MEDIA_GROUP = "media_group"
    OUTLET = "outlet"                   # a news brand / domain
    PARTY = "party"
    GOVT_BODY = "govt_body"             # ministry, SOE holding, Danantara, DPR
    CONCESSION = "concession"           # HGU / IUP plantation permit


class EdgeType(str, Enum):
    OWNS = "owns"                       # shareholding, optional pct
    CONTROLS = "controls"               # ultimate / beneficial control
    MEMBER_OF_GROUP = "member_of_group" # company -> business_group
    BOARD_SEAT = "board_seat"           # person -> company; role = commissioner/director/...
    HELD_OFFICE = "held_office"         # person -> govt_body; role = minister, MP, ...
    PARTY_ROLE = "party_role"           # person -> party; role = chair, member, ...
    FAMILY_OF = "family_of"             # person -> person; role = spouse/child/sibling
    FINANCES = "finances"               # bank -> company/group; amount_usd, year
    HOLDS_CONCESSION = "holds_concession"
    OWNS_MEDIA = "owns_media"           # person/group -> media_group
    PUBLISHES = "publishes"             # media_group -> outlet
    COALITION = "coalition"             # party -> govt_body (gov coalition), time-bound
    CONVICTED_IN = "convicted_in"       # only with a link to the final verdict


class SourceType(str, Enum):
    ANNUAL_REPORT = "annual_report"
    EXCHANGE_FILING = "exchange_filing"
    GOVT_REGISTRY = "govt_registry"     # AHU, KPK LHKPN, KPU, ESDM, ATR/BPN
    COURT_RECORD = "court_record"
    NGO_DATASET = "ngo_dataset"         # Forests & Finance, TuK, Auriga, Trase
    NEWS = "news"
    COMPANY_WEBSITE = "company_website"
    OTHER = "other"


class Confidence(str, Enum):
    HIGH = "high"      # primary source (filing, registry, verdict)
    MEDIUM = "medium"  # reputable secondary (major outlet, established NGO)
    LOW = "low"        # single secondary source, needs confirmation


# Which (source_type -> minimum allowed confidence) combos are acceptable for
# sensitive edge types. Family ties and convictions need stronger evidence.
SENSITIVE_EDGES = {EdgeType.FAMILY_OF, EdgeType.CONVICTED_IN}


@dataclass
class Node:
    id: str
    type: NodeType
    name: str
    aliases: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)


@dataclass
class Edge:
    source_id: str
    target_id: str
    type: EdgeType
    source_url: str
    source_type: SourceType
    confidence: Confidence
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pct: Optional[float] = None
    amount_usd: Optional[float] = None
    note: Optional[str] = None

    def active_on(self, d: date) -> bool:
        """True if the relationship was in effect on date d.

        Unknown start/end dates are treated as open-ended, which is the
        generous assumption. Analysis code should report how many edges
        rely on that assumption.
        """
        if self.start_date and d < self.start_date:
            return False
        if self.end_date and d > self.end_date:
            return False
        return True


class SchemaError(ValueError):
    pass


def validate_edge(e: Edge, nodes: dict[str, Node]) -> None:
    if e.source_id not in nodes:
        raise SchemaError(f"unknown source node {e.source_id!r}")
    if e.target_id not in nodes:
        raise SchemaError(f"unknown target node {e.target_id!r}")

    parsed = urlparse(e.source_url or "")
    is_web = parsed.scheme in ("http", "https") and bool(parsed.netloc)
    # doc:<doc_id>#p<page> points at an archived primary document listed in
    # data/raw/documents.csv (checked by the loader against the registry).
    is_doc = parsed.scheme == "doc" and bool(parsed.path)
    if not (is_web or is_doc):
        raise SchemaError(f"edge {e.source_id}->{e.target_id} has no valid source_url")

    if e.start_date and e.end_date and e.end_date < e.start_date:
        raise SchemaError(f"edge {e.source_id}->{e.target_id} ends before it starts")

    if e.pct is not None and not (0 <= e.pct <= 100):
        raise SchemaError(f"pct out of range on {e.source_id}->{e.target_id}")

    if e.type in SENSITIVE_EDGES and e.confidence == Confidence.LOW:
        raise SchemaError(
            f"{e.type.value} edges require medium or high confidence "
            f"({e.source_id}->{e.target_id})"
        )

    if e.type == EdgeType.CONVICTED_IN and e.source_type != SourceType.COURT_RECORD:
        raise SchemaError("convicted_in edges must cite the court record itself")
