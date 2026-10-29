"""md(1_rules/, 2_concepts.md, 3_relations.md)와 온톨로지 파일(game_ui.ttl, rules.ttl)의 정의 일치 검사"""

import re
from pathlib import Path

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS, SH, Namespace
from rdflib.plugins.sparql import prepareQuery

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


def test_tagged_relations(graph):
    """학습 데이터가 라벨링 태깅인 관계 행과 labelingSubject·labelingObject 선언이 같음"""
    md_rows = {
        (name, *(frozenset(side.split(" ∧ ")) for side in sig.split(" → ")))
        for name, sig, _, data, _ in rows(md("3_relations.md"), 5)[1:]
        if data == "라벨링 태깅"
    }
    ttl_rows = {
        (local(r), *(frozenset(local(c) for c in graph.objects(r, p)) for p in (GQ.labelingSubject, GQ.labelingObject)))
        for r in set(graph.subjects(GQ.labelingSubject, None))
    }
    assert md_rows == ttl_rows


def signature(text):
    name, args = re.match(r"(\w+)\((.*)\)", text).groups()
    return name, len(args.split(","))


def test_measurements(graph):
    md_sigs = {signature(r[0]) for r in rows(md("3_relations.md"), 4)[1:]}
    ttl_sigs = {signature(comment(graph, local(s))) for s in graph.subjects(RDFS.subClassOf, GQ.Measurement)}
    assert md_sigs == ttl_sigs


def test_rules():
    """규칙 목록의 규칙마다 SHACL 형상이 있고, 형상마다 결과 메시지가 자기 규칙 ID로 시작"""
    rules = rdflib.Graph().parse(ROOT / "rules.ttl")
    table = md("1_rules/README.md").split("## 규칙 목록")[1].split("\n## ")[0]
    md_ids = {re.match(r"\[(R-\d{3})\]", r[0]).group(1) for r in rows(table, 3)[1:]}
    shapes = {local(s): s for s in rules.subjects(RDF.type, SH.NodeShape)}
    assert md_ids == {re.match(r"R-\d{3}", name).group() for name in shapes}
    for name, shape in shapes.items():
        message = str(rules.value(rules.value(shape, SH.sparql), SH.message))
        assert message.split()[0] == name[:5], name


def test_rule_messages():
    """결과 메시지 형식 "<규칙 ID> <대상 ...>"이 질의와 맞음 (validate.py가 메시지에서 대상을 읽음)
    - 대상 변수: SELECT 변수와 순서까지 같음
    - "|": 마지막 변수 앞에만, 그 변수는 GROUP_CONCAT 목록"""
    rules = rdflib.Graph().parse(ROOT / "rules.ttl")
    for shape in rules.subjects(RDF.type, SH.NodeShape):
        sparql = rules.value(shape, SH.sparql)
        prefixes = {str(rules.value(d, SH.prefix)): str(rules.value(d, SH.namespace)) for d in rules.objects(rules.value(sparql, SH.prefixes), SH.declare)}
        query = str(rules.value(sparql, SH.select))
        projected = [str(v) for v in prepareQuery(query, initNs=prefixes).algebra["PV"]]
        _, *parts = str(rules.value(sparql, SH.message)).split()
        variables = [re.fullmatch(r"\{[?$](\w+)\}", p).group(1) for p in parts if p != "|"]
        assert variables == projected, local(shape)
        lists = re.findall(r"GROUP_CONCAT\(.*?\)\s+AS\s+\?(\w+)", query, re.S)
        if "|" in parts:
            assert parts.index("|") == len(parts) - 2 and lists == variables[-1:], local(shape)
        else:
            assert not lists, local(shape)


def test_rule_requirements(graph):
    """형상마다 선언한 파라미터·측정값 클래스가 질의가 읽는 것과 같음"""
    rules = rdflib.Graph().parse(ROOT / "rules.ttl")
    gqr = Namespace("https://github.com/Kiyeon-Nam/game-qa/rules#")
    measurements = {local(s) for s in graph.subjects(RDFS.subClassOf, GQ.Measurement)}
    for shape in rules.subjects(RDF.type, SH.NodeShape):
        query = str(rules.value(rules.value(shape, SH.sparql), SH.select))
        params = {str(p) for p in rules.objects(shape, gqr.param)}
        assert params == set(re.findall(r'gqr:name\s+"(\w+)"', query)), local(shape)
        declared = {local(rules.value(m, gqr.measurement)) for m in rules.objects(shape, gqr.measures)}
        assert declared == set(re.findall(r"a gq:(\w+)", query)) & measurements, local(shape)
