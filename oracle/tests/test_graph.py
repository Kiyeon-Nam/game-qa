import json
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Literal
from rdflib.namespace import XSD

from graph import GQ, INST, instance_id, measurement_class, ontology, to_graph

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


def load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_example_converts_all_items():
    result = load("examples/inference.json")
    g = to_graph(result)
    for x in result["instances"]:
        assert (INST[str(x["id"])], RDF.type, GQ[x["class"]]) in g
    for r in result["relations"]:
        assert (INST[str(r["subject"])], GQ[r["type"]], INST[str(r["object"])]) in g
    assert len(list(g.subjects(GQ.value, None))) == len(result["measurements"])


def test_measurement_node():
    result = {"instances": [], "relations": [], "measurements": [{"name": "distance", "args": [3, 1], "value": 0.2}]}
    g = to_graph(result)
    (n,) = g.subjects(RDF.type, GQ.Distance)
    assert g.value(n, GQ.measuredSubject) == INST["3"]
    assert g.value(n, GQ.measuredObject) == INST["1"]
    assert g.value(n, GQ.value) == Literal(0.2, datatype=XSD.double)


def test_instance_id_round_trip():
    assert instance_id(INST["12"]) == 12
    assert instance_id(INST["ScreenBounds"]) == "ScreenBounds"


def test_schema_vocabulary_exists_in_ontology():
    """추론 결과 형식의 클래스·관계·측정값 이름이 모두 온톨로지에 있음"""
    onto = ontology()
    schema = load("inference.schema.json")["properties"]
    for name in schema["relations"]["items"]["properties"]["type"]["enum"]:
        assert (GQ[name], RDF.type, OWL.ObjectProperty) in onto, name
    for name in schema["measurements"]["items"]["properties"]["name"]["enum"]:
        assert (measurement_class(name), RDFS.subClassOf, GQ.Measurement) in onto, name
    labels = load("examples/label.json")["categories"]
    for c in labels:
        assert (GQ[c["name"]], GQ.classId, None) in onto, c["name"]
