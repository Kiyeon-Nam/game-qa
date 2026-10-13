"""md(2_concepts.md, 3_relations.md)와 온톨로지 파일(game_ui.ttl)의 정의 일치 검사"""

import re
from pathlib import Path

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS, Namespace

ROOT = Path(__file__).resolve().parents[1]
GQ = Namespace("https://github.com/Kiyeon-Nam/game-qa/ontology#")
AXES = ("역할", "배치", "충돌성", "지지 방식", "그리기 층", "특수")


@pytest.fixture(scope="module")
def graph():
    return rdflib.Graph().parse(ROOT / "game_ui.ttl")


def md(name):
    return (ROOT / name).read_text(encoding="utf-8")


def rows(text, columns):
    """표의 행을 칸 목록으로. 칸 수가 columns인 행만"""
    out = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == columns and not set(cells[0]) <= {"-"}:
            out.append(cells)
    return out


def local(uri):
    return str(uri).split("#")[1]


def comment(g, name):
    return str(g.value(GQ[name], RDFS.comment))


def test_concepts(graph):
    concepts = [r for r in rows(md("2_concepts.md"), 5) if r[0] in AXES]
    md_names = {r[1] for r in concepts}
    ttl_names = {local(s) for s in graph.subjects(GQ.axis, None)} | {"ScreenBounds"}
    assert md_names == ttl_names
    for axis, name, parent, definition, _ in concepts:
        if axis == "특수":
            assert comment(graph, name).startswith(definition), name
            continue
        assert comment(graph, name) == definition, name
        assert str(graph.value(GQ[name], GQ.axis)) == axis, name
        parents = {local(o) for o in graph.objects(GQ[name], RDFS.subClassOf)}
        assert parents == ({parent} if parent else set()), name


def test_labeling_classes(graph):
    text = md("2_concepts.md").split("## 조합 개념과 라벨링 클래스")[1]
    for class_id, name, combination in rows(text, 3)[1:]:
        assert graph.value(GQ[name], GQ.classId).toPython() == int(class_id), name
        expected = set(combination.split(" ∧ "))
        if expected == {name}:
            continue
        equivalent = graph.value(GQ[name], OWL.equivalentClass)
        members = rdflib.collection.Collection(graph, graph.value(equivalent, OWL.intersectionOf))
        assert {local(m) for m in members} == expected, name


def class_names(g, node):
    """클래스 또는 owl:unionOf의 이름 집합"""
    union = g.value(node, OWL.unionOf)
    if union is None:
        return {local(node)}
    return {local(m) for m in rdflib.collection.Collection(g, union)}


def test_relations(graph):
    relations = rows(md("3_relations.md"), 5)[1:]
    md_names = {r[0] for r in relations}
    assert md_names == {local(s) for s in graph.subjects(RDF.type, OWL.ObjectProperty) if graph.value(s, RDFS.domain) != GQ.Measurement}
    for name, signature, meaning, _, _ in relations:
        assert comment(graph, name) == meaning, name
        pairs = [pair.split(" → ") for pair in signature.split(", ")]
        domain, range_ = " ".join(d for d, _ in pairs), " ".join(r for _, r in pairs)
        for cls in class_names(graph, graph.value(GQ[name], RDFS.domain)):
            assert cls in domain, (name, cls)
        for cls in class_names(graph, graph.value(GQ[name], RDFS.range)):
            assert cls in range_, (name, cls)


def signature(text):
    name, args = re.match(r"(\w+)\((.*)\)", text).groups()
    return name, len(args.split(","))


def test_measurements(graph):
    md_sigs = {signature(r[0]) for r in rows(md("3_relations.md"), 4)[1:]}
    ttl_sigs = {signature(comment(graph, local(s))) for s in graph.subjects(RDFS.subClassOf, GQ.Measurement)}
    assert md_sigs == ttl_sigs
