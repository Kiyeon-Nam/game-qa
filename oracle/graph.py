"""판정 파이프라인 ④: 추론 결과(schemas/inference.schema.json)를 RDF 그래프로 변환

- 인스턴스: inst:<id>, 라벨링 클래스로 타입 지정. 상위 개념은 검증 시 온톨로지로 추론
- ScreenBounds: inst:ScreenBounds 하나
- 관계: 인스턴스 사이 속성
- 측정값: Measurement 노드 (measuredSubject, measuredObject, value)
"""

import re

from rdflib import RDF, BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

from game_qa.ontology.game_ui import GQ

INST = Namespace("urn:game-qa:instance:")
SCREEN = "ScreenBounds"


def node(ref):
    return INST[str(ref)]


def instance_id(uri):
    """인스턴스 URI를 추론 결과의 id(또는 "ScreenBounds")로"""
    ref = str(uri).removeprefix(str(INST))
    return ref if ref == SCREEN else int(ref)


def measurement_class(name):
    """측정값 이름(snake_case)을 온톨로지 클래스로. overlap_ratio → OverlapRatio"""
    return GQ["".join(part.capitalize() for part in name.split("_"))]


def measurement_name(cls):
    """measurement_class의 역. OverlapRatio → overlap_ratio"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", str(cls).removeprefix(str(GQ))).lower()


def to_graph(result):
    g = Graph()
    g.bind("gq", GQ)
    g.bind("inst", INST)
    for x in result["instances"]:
        g.add((node(x["id"]), RDF.type, GQ[x["class"]]))
    g.add((node(SCREEN), RDF.type, GQ.ScreenBounds))
    for r in result["relations"]:
        g.add((node(r["subject"]), GQ[r["type"]], node(r["object"])))
    for m in result["measurements"]:
        n = BNode()
        g.add((n, RDF.type, measurement_class(m["name"])))
        g.add((n, GQ.measuredSubject, node(m["args"][0])))
        if len(m["args"]) > 1:
            g.add((n, GQ.measuredObject, node(m["args"][1])))
        g.add((n, GQ.value, Literal(m["value"], datatype=XSD.double)))
    return g

