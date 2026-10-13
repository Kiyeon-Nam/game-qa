"""판정 파이프라인 ⑤: 그래프를 규칙 SHACL 형상(rules.ttl)으로 검증

- 검증 엔진: pySHACL. 그래프 저장소는 Oxigraph(oxrdflib)로 두어 SPARQL을 Oxigraph가 실행
  (rdflib 기본 저장소는 조인이 많은 규칙에서 프레임 하나에 수십 초 이상)
- 상위 개념: 검증 시 추론 대신 온톨로지의 하위 클래스 관계로 인스턴스 타입을 미리 펼침
- 검증 전 확인: 규칙이 읽는 파라미터, 규칙이 쓰는 측정값의 누락 (빠지면 위반이 조용히 바뀜)
"""

import re
from functools import cache
from itertools import combinations
from pathlib import Path

import owlrl
from pyshacl import validate as shacl_validate
from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace
from rdflib.namespace import SH, XSD

from graph import GQ, instance_id, ontology, to_graph

GQR = Namespace("https://github.com/Kiyeon-Nam/game-qa/rules#")
RULES = Path(__file__).resolve().parent / "rules.ttl"


@cache
def superclasses():
    """클래스 이름별 상위 클래스 집합 (owl:equivalentClass 교집합 포함)"""
    onto = ontology()
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(onto)
    out = {}
    for c, sup in onto.subject_objects(RDFS.subClassOf):
        out.setdefault(c, set()).add(sup)
    return out


@cache
def rules():
    return Graph().parse(RULES)


def has(cls, concept):
    return GQ[cls] == GQ[concept] or GQ[concept] in superclasses().get(GQ[cls], ())


def data_graph(result, params, store="Oxigraph"):
    g = Graph(store=store)
    for t in to_graph(result):
        g.add(t)
    for s, c in list(g.subject_objects(RDF.type)):
        for sup in superclasses().get(c, ()):
            g.add((s, RDF.type, sup))
    # R-003 조건 2가 하위 개념을 찾을 때 쓰는 온톨로지 정보
    for t in ontology().triples((None, RDFS.subClassOf, None)):
        g.add(t)
    for t in ontology().triples((None, GQ.axis, None)):
        g.add(t)
    for name, value in params.items():
        n = BNode()
        g.add((n, GQR.name, Literal(name)))
        g.add((n, GQR.value, Literal(value, datatype=XSD.double)))
    return g


def required_params():
    """규칙 질의가 읽는 파라미터 이름"""
    queries = " ".join(str(q) for q in rules().objects(None, SH.select))
    return set(re.findall(r'gqr:name\s+"(\w+)"', queries))


def missing_measurements(result):
    """규칙이 쓰는 측정값 중 추론 결과에 없는 것. (측정값 이름, 인자) 목록"""
    have = {(m["name"], tuple(m["args"])) for m in result["measurements"]}
    classes = {x["id"]: x["class"] for x in result["instances"]}

    def of(*concepts):
        return [i for i, c in classes.items() if all(has(c, k) for k in concepts)]

    world = of("Display", "World")
    need = [("distance", (i, e)) for i in world for e in of("Entity")]
    need += [("foreground_coverage", (i,)) for i in world + of("GroundedObject")]
    need += [("overlap_ratio", (a,)) for a in of("Character") + of("LooseObject")]
    need += [("support_gap", (o,)) for o in of("GroundedObject")]
    need += [("edge_distance", (q, c)) for q in of("Equipment") for c in of("Character")]
    need += [("contain_ratio", (p, x)) for p in of("UIPanel") for x in of("TextLabel")]
    missing = [n for n in need if n not in have]
    for a, b in combinations(of("HUDElement"), 2):
        if ("mutual_overlap", (a, b)) not in have and ("mutual_overlap", (b, a)) not in have:
            missing.append(("mutual_overlap", (a, b)))
    return missing


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
        rule, *targets = str(report.value(r, SH.resultMessage)).split()
        found.add((rule, tuple(instance_id(t) for t in targets)))
    return sorted(found)
