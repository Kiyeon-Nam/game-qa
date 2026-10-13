"""라벨링 클래스와 개념의 대응. 정본은 ontology/2_concepts.md의 조합 표"""

CLASS_CONCEPTS = {
    "Character": {"Entity", "Character"},
    "LooseObject": {"Entity", "Object", "Free"},
    "Equipment": {"Entity", "Object", "Attached"},
    "GroundedObject": {"Entity", "Object", "Grounded"},
    "Terrain": {"Structure", "Solid"},
    "Platform": {"Structure", "OneWay"},
    "ForegroundDecoration": {"Structure", "Foreground"},
    "HealthBar": {"Display", "HealthDisplay", "World"},
    "HUDElement": {"Display", "ScreenFixed"},
    "UIPanel": {"Panel", "ScreenFixed"},
    "TextLabel": {"Text", "ScreenFixed"},
}


def has(cls, *concepts):
    return set(concepts) <= CLASS_CONCEPTS[cls]
