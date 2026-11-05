"""판정 파이프라인 ⑤: 그래프를 규칙 SHACL 형상(ontology/rules.ttl)으로 검증

- 검증 엔진: pySHACL. 그래프 저장소는 Oxigraph(oxrdflib)로 두어 SPARQL을 Oxigraph가 실행
  (rdflib 기본 저장소는 조인이 많은 규칙에서 프레임 하나에 수십 초 이상)
- 상위 개념: 검증 시 추론 대신 인스턴스·측정값 타입을 상위 개념(game_qa.ontology)으로 미리 펼침
- 검증 전 확인: 규칙 형상이 선언한 파라미터·측정값의 누락 (빠지면 위반이 조용히 바뀜)
"""

from functools import cache
from pathlib import Path

from pyshacl import validate as shacl_validate
from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace
from rdflib.namespace import OWL, SH, XSD

from game_qa.ontology.game_ui import graph, has, local, superclasses, symmetric_measurements
from game_qa.oracle.graph import GQ, instance_id, measurement_name, to_graph

GQR = Namespace("https://github.com/Kiyeon-Nam/game-qa/rules#")
RULES = Path(__file__).resolve().parents[1] / "ontology" / "rules.ttl"


@cache
def rules():
    return Graph().parse(RULES)


def data_graph(result, params, store="Oxigraph"):
    g = Graph(store=store)
    for t in to_graph(result):
        g.add(t)
    for s, c in list(g.subject_objects(RDF.type)):
        for sup in superclasses().get(local(c), ()):
            g.add((s, RDF.type, GQ[sup]))
    # R-003 조건 2가 하위 개념을 찾을 때 쓰는 온톨로지 정보
    for t in graph().triples((None, RDFS.subClassOf, None)):
        g.add(t)
    for t in graph().triples((None, GQ.axis, None)):
        g.add(t)
    for name, value in params.items():
        n = BNode()
        g.add((n, GQR.name, Literal(name)))
        g.add((n, GQR.value, Literal(value, datatype=XSD.double)))
    return g


def required_params():
    """규칙 형상이 선언한 파라미터 이름 (gqr:param)"""
    return {str(p) for p in rules().objects(None, GQR.param)}


def relation(node):
    """gqr:relation 값을 (관계 이름, 반대 방향 여부)로. 없으면 None"""
    g = rules()
    if node is None:
        return None
    inverse = g.value(node, OWL.inverseOf)
    return (local(inverse), True) if inverse is not None else (local(node), False)


@cache
def required_measurements():
    """규칙 형상이 선언한 측정값 (gqr:measures). (측정값 이름, 주체 개념, 대상 개념, 관계) 집합"""
    g = rules()
    return {
        (
            measurement_name(g.value(n, GQR.measurement)),
            frozenset(map(local, g.objects(n, GQR.subject))),
            frozenset(map(local, g.objects(n, GQR.object))),
            relation(g.value(n, GQR.relation)),
        )
        for n in g.objects(None, GQR.measures)
    }


def missing_measurements(result):
    """규칙이 선언한 측정값 중 추론 결과에 없는 것. (측정값 이름, 인자) 목록, 이름·인자 순"""
    have = {(m["name"], tuple(m["args"])) for m in result["measurements"]}
    classes = {x["id"]: x["class"] for x in result["instances"]}
    links = {}
    for r in result["relations"]:
        links.setdefault(r["type"], []).append((r["subject"], r["object"]))
    symmetric = {measurement_name(GQ[c]) for c in symmetric_measurements()}

    def of(concepts):
        return [i for i, c in classes.items() if has(c, *concepts)]

    def linked(rel, subject, object_):
        kind, inverse = rel
        pairs = [p[::-1] if inverse else p for p in links.get(kind, [])]
        return [(s, o) for s, o in pairs if s in classes and o in classes and has(classes[s], *subject) and has(classes[o], *object_)]

    missing = set()
    for name, subject, object_, rel in required_measurements():
        if rel:
            need = linked(rel, subject, object_)
        elif object_:
            need = [(i, e) for i in of(subject) for e in of(object_)]
        else:
            need = [(i,) for i in of(subject)]
        if name in symmetric:
            need = {tuple(sorted(p)) for p in need if p[0] != p[1]}
        for args in need:
            if (name, args) not in have and not (name in symmetric and (name, args[::-1]) in have):
                missing.add((name, args))
    return sorted(missing)


def violations(result, params, store="Oxigraph"):
    """추론 결과의 위반 목록. (규칙 ID, 대상 인스턴스 id 목록). store="Memory"는 rdflib 기본 저장소"""
    missing = required_params() - params.keys()
    if missing:
        raise ValueError(f"파라미터 누락: {', '.join(sorted(missing))}")
    absent = missing_measurements(result)
    if absent:
        raise ValueError(f"측정값 누락: {absent[:5]}")
    _, report, _ = shacl_validate(data_graph(result, params, store), shacl_graph=rules(), inference="none", advanced=True, inplace=True)
    found = set()
    for r in report.subjects(SH.resultSeverity, None):
        rule, *rest = str(report.value(r, SH.resultMessage)).split()
        ordered, _, unordered = " ".join(rest).partition("|")
        targets = [instance_id(t) for t in ordered.split()] + sorted(instance_id(t) for t in unordered.split())
        found.add((rule, tuple(targets)))
    return sorted(found)
