"""온톨로지 파일(game_ui.ttl) 읽기

- 상위 개념: OWL-RL 추론 결과의 rdfs:subClassOf 중 이름 있는 온톨로지 클래스 (자신 포함)
- 라벨링 클래스: classId가 있는 클래스
- 태깅 관계: labelingSubject·labelingObject가 있는 관계
  - 주체·대상: 각 개념을 모두 가진 라벨링 클래스
"""

from functools import cache
from pathlib import Path

import owlrl
from rdflib import RDFS, Graph, Namespace, URIRef

GQ = Namespace("https://github.com/Kiyeon-Nam/game-qa/ontology#")
ONTOLOGY = Path(__file__).resolve().parent / "game_ui.ttl"


@cache
def graph():
    """읽기 전용"""
    return Graph().parse(ONTOLOGY)


def local(uri):
    return str(uri).removeprefix(str(GQ))


def named(uri):
    return isinstance(uri, URIRef) and str(uri).startswith(str(GQ))


@cache
def superclasses():
    """클래스 이름 → 자신과 상위 개념 이름 집합"""
    g = Graph()
    g += graph()
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    out = {}
    for c, sup in g.subject_objects(RDFS.subClassOf):
        if named(c) and named(sup):
            out.setdefault(local(c), set()).add(local(sup))
    return {c: frozenset(sups) for c, sups in out.items()}


@cache
def class_ids():
    """라벨링 클래스 이름 → classId"""
    return {local(c): int(i) for c, i in graph().subject_objects(GQ.classId)}


def has(cls, *concepts):
    """라벨링 클래스가 개념을 모두 가짐"""
    return set(concepts) <= superclasses()[cls]


@cache
def tagged_relations():
    """태깅 관계 이름 → (주체 라벨링 클래스 집합, 대상 라벨링 클래스 집합). 관계 이름 순"""
    g = graph()

    def having(r, prop):
        concepts = {local(c) for c in g.objects(r, prop)}
        return {cls for cls in class_ids() if has(cls, *concepts)}

    relations = sorted(set(g.subjects(GQ.labelingSubject, None)), key=local)
    return {local(r): (having(r, GQ.labelingSubject), having(r, GQ.labelingObject)) for r in relations}
