"""온톨로지 파일(game_ui.ttl)에서 라벨링 클래스·태깅 관계 정의 읽기

- 라벨링 클래스: classId가 있는 클래스
- 클래스별 개념: 자신, 상위 클래스(rdfs:subClassOf), 동치 교집합(owl:intersectionOf) 구성 개념과 그 상위 개념
- 태깅 관계: labelingSubject가 있는 관계
  - 주체: labelingSubject 개념을 모두 가진 라벨링 클래스, 대상: rdfs:range 개념을 가진 라벨링 클래스
"""

from functools import cache
from pathlib import Path

from rdflib import OWL, RDFS, Graph, Namespace
from rdflib.collection import Collection

GQ = Namespace("https://github.com/Kiyeon-Nam/game-qa/ontology#")
ONTOLOGY = Path(__file__).resolve().parent / "game_ui.ttl"


@cache
def graph():
    """읽기 전용. 수정이 필요하면 Graph().parse(ONTOLOGY)로 새로 읽기"""
    return Graph().parse(ONTOLOGY)


def local(uri):
    return str(uri).removeprefix(str(GQ))


@cache
def class_ids():
    """라벨링 클래스 이름 → classId"""
    return {local(c): int(i) for c, i in graph().subject_objects(GQ.classId)}


def parents(c):
    g = graph()
    out = set(g.objects(c, RDFS.subClassOf))
    for eq in g.objects(c, OWL.equivalentClass):
        out |= set(Collection(g, g.value(eq, OWL.intersectionOf)))
    return out


@cache
def class_concepts():
    """라벨링 클래스 이름 → 개념 이름 집합"""
    out = {}
    for cls in class_ids():
        seen, todo = set(), [GQ[cls]]
        while todo:
            c = todo.pop()
            if c not in seen:
                seen.add(c)
                todo += parents(c)
        out[cls] = frozenset(local(c) for c in seen)
    return out


def has(cls, *concepts):
    return set(concepts) <= class_concepts()[cls]


@cache
def tagged_relations():
    """태깅 관계 이름 → (주체 라벨링 클래스 집합, 대상 라벨링 클래스 집합). 관계 이름 순"""
    g = graph()

    def having(concepts):
        return {cls for cls in class_ids() if has(cls, *concepts)}

    relations = sorted(set(g.subjects(GQ.labelingSubject, None)), key=local)
    return {
        local(r): (having({local(c) for c in g.objects(r, GQ.labelingSubject)}), having({local(g.value(r, RDFS.range))}))
        for r in relations
    }
