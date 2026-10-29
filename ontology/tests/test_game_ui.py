from game_qa.ontology.game_ui import class_concepts, class_ids, tagged_relations


def test_class_concepts_follow_intersection_and_superclasses():
    concepts = class_concepts()
    assert concepts.keys() == class_ids().keys()
    assert concepts["HealthBar"] == {"HealthBar", "HealthDisplay", "Display", "World"}
    assert concepts["Character"] == {"Character", "Entity"}


def test_tagged_relations_use_labeling_subject_and_range():
    assert tagged_relations() == {
        "attachedTo": ({"Equipment"}, {"Character"}),
        "represents": ({"HealthBar"}, {"Character", "LooseObject", "Equipment", "GroundedObject"}),
    }
