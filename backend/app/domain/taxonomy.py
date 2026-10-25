"""The one authoritative defect taxonomy.

Everything that depends on "which defect classes exist, what category they belong to, and
which of them the vision model can currently detect" derives it from here: the category of a
detection, the coverage statement, the limitation text, and the facts given to the advisor.
Do not copy these lists anywhere else.

Inventory source: the ECX defect rubric in the project docs (6 primary + 7 secondary = 13).
Have a domain expert confirm it before treating it as an official standard.

A class is "scanned" when it has a `vision_label`: the exact `class_name` the vision service
emits for it. When the vision model learns a new class, add its label here (one line). When
vision emits a label that is not listed, the assessment fails instead of guessing a category.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import UnknownDefectClassError, VisionBadResponseError


class DefectCategory(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


# How the vision service spells categories on the wire (its `DetectedBean.category`).
# Used only to detect drift between the two services, never to decide a category.
_VISION_CATEGORY_NAMES: dict[str, DefectCategory] = {
    "Primary Defect": DefectCategory.PRIMARY,
    "Secondary Defect": DefectCategory.SECONDARY,
}


@dataclass(frozen=True, slots=True)
class DefectClass:
    key: str
    name: str
    category: DefectCategory
    vision_label: str | None = None


ECX_DEFECT_CLASSES: tuple[DefectClass, ...] = (
    # Primary (severe)
    DefectClass("full_black", "Full Black", DefectCategory.PRIMARY, vision_label="Full Black"),
    DefectClass("full_sour", "Full Sour / Stinker", DefectCategory.PRIMARY),
    DefectClass("pod", "Pod", DefectCategory.PRIMARY),
    DefectClass("fungus_mold", "Fungus / Mold", DefectCategory.PRIMARY),
    DefectClass("severe_insect_damage", "Severe Insect Damage", DefectCategory.PRIMARY),
    DefectClass("foreign_matter", "Foreign Matter", DefectCategory.PRIMARY),
    # Secondary (minor)
    DefectClass(
        "partial_black", "Partial Black", DefectCategory.SECONDARY, vision_label="Partial Black"
    ),
    DefectClass("partial_sour", "Partial Sour", DefectCategory.SECONDARY),
    DefectClass(
        "parchment_husk",
        "Coffee Husk / Parchment",
        DefectCategory.SECONDARY,
        vision_label="Coffee Husk / Parchment",
    ),
    DefectClass("floater", "Floater / Chalky", DefectCategory.SECONDARY),
    DefectClass("immature", "Immature / Quaker", DefectCategory.SECONDARY),
    DefectClass("broken_chipped", "Broken / Chipped", DefectCategory.SECONDARY),
    DefectClass("slight_insect_damage", "Slight Insect Damage", DefectCategory.SECONDARY),
)


class DefectTaxonomy:
    """Lookup and coverage over a fixed set of defect classes."""

    def __init__(self, classes: Iterable[DefectClass]) -> None:
        ordered = tuple(classes)

        keys = [c.key for c in ordered]
        if len(set(keys)) != len(keys):
            raise ValueError("defect class keys must be unique")
        
        labels = [c.vision_label for c in ordered if c.vision_label is not None]
        if len(set(labels)) != len(labels):
            raise ValueError("vision labels must be unique")
        
        self._classes = ordered
        self._by_label: dict[str, DefectClass] = {
            c.vision_label: c for c in ordered if c.vision_label is not None
        }

    @property
    def all(self) -> tuple[DefectClass, ...]:
        return self._classes

    @property
    def scanned(self) -> tuple[DefectClass, ...]:
        return tuple(c for c in self._classes if c.vision_label is not None)

    @property
    def not_scanned(self) -> tuple[DefectClass, ...]:
        return tuple(c for c in self._classes if c.vision_label is None)

    def from_vision_label(self, label: str) -> DefectClass:
        try:
            return self._by_label[label]
        except KeyError:
            raise UnknownDefectClassError(
                f"vision label {label!r} is not in the defect taxonomy"
            ) from None

    def resolve(self, label: str, reported_category: str | None) -> DefectClass:
        """Map a vision label to a class, and fail if vision's own category disagrees.

        Our taxonomy decides the category. If vision also reports one and it differs, the two
        services have drifted apart; continuing would silently trust one of them, so we stop.
        """
        defect = self.from_vision_label(label)
        if reported_category is not None:
            reported = _VISION_CATEGORY_NAMES.get(reported_category)
            if reported is not defect.category:
                raise VisionBadResponseError(
                    f"vision reported category {reported_category!r} for {label!r}, "
                    f"but the taxonomy says {defect.category.value!r}"
                )
        return defect


ECX_TAXONOMY = DefectTaxonomy(ECX_DEFECT_CLASSES)
