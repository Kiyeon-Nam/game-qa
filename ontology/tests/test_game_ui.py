from game_qa.ontology.game_ui import class_ids, superclasses, tagged_relations


def test_superclasses_follow_intersection_and_subclass():
    assert class_ids().keys() <= superclasses().keys()
    assert superclasses()["HealthBar"] == {"HealthBar", "HealthDisplay", "Display", "World"}
    assert superclasses()["Character"] == {"Character", "Entity"}


def test_tagged_relations_use_labeling_subject_and_object():
    assert tagged_relations() == {
        "attachedTo": ({"Equipment"}, {"Character"}),
        "represents": ({"HealthBar"}, {"Character", "LooseObject", "Equipment", "GroundedObject"}),
    }
