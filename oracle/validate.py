"""판정 파이프라인 ⑤: 그래프를 규칙 SHACL 형상(rules.ttl)으로 검증

- 검증 엔진: pySHACL. 그래프 저장소는 Oxigraph(oxrdflib)로 두어 SPARQL을 Oxigraph가 실행
  (rdflib 기본 저장소는 조인이 많은 규칙에서 프레임 하나에 수십 초 이상)
- 상위 개념: 검증 시 추론 대신 온톨로지의 하위 클래스 관계로 인스턴스 타입을 미리 펼침
"""

import re
from functools import cache
from pathlib import Path

import owlrl
from pyshacl import validate as shacl_validate
from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace
from rdflib.namespace import SH, XSD

from graph import instance_id, ontology, to_graph

GQR = Namespace("https://github.com/Kiyeon-Nam/game-qa/rules#")
RULES = Path(__file__).resolve().parent / "rules.ttl"


@cache
def superclasses():
    """클래스별 상위 클래스 집합 (owl:equivalentClass 교집합 포함)"""
    onto = ontology()
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(onto)
    out = {}
    for c, sup in onto.subject_objects(RDFS.subClassOf):
        out.setdefault(c, set()).add(sup)
    return out


@cache
def rules():
    return Graph().parse(RULES)


def data_graph(result, params, store="Oxigraph"):
    g = Graph(store=store)
    for t in to_graph(result):
        g.add(t)
    for s, c in list(g.subject_objects(RDF.type)):
        for sup in superclasses().get(c, ()):
            g.add((s, RDF.type, sup))
    for name, value in params.items():
        n = BNode()
        g.add((n, GQR.name, Literal(name)))
        g.add((n, GQR.value, Literal(value, datatype=XSD.double)))
    return g


def required_params():
    """규칙이 읽는 파라미터 이름. 빠지면 해당 규칙이 위반을 내지 않으므로 검증 전에 확인"""
    return set(re.findall(r'gqr:name "(\w+)"', RULES.read_text(encoding="utf-8")))


def violations(result, params, store="Oxigraph"):
    """추론 결과의 위반 목록. (규칙 ID, 대상 인스턴스 id 목록). store="Memory"는 rdflib 기본 저장소"""
    missing = required_params() - params.keys()
    if missing:
        raise ValueError(f"파라미터 누락: {', '.join(sorted(missing))}")
    _, report, _ = shacl_validate(data_graph(result, params, store), shacl_graph=rules(), inference="none", advanced=True, inplace=True)
    found = set()
    for r in report.subjects(SH.resultSeverity, None):
        rule, *targets = str(report.value(r, SH.resultMessage)).split()
        found.add((rule, tuple(instance_id(t) for t in targets)))
    return sorted(found)
