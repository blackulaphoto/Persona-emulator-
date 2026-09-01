"""Eligibility rules for canonical evidence entering downstream psychology."""
from typing import Iterable, Optional, Set


def _event_ids(values: Optional[Iterable[str]]) -> Optional[Set[str]]:
    return {str(value) for value in values} if values is not None else None


def exposure_has_provenance(item, valid_event_ids: Optional[Iterable[str]] = None) -> bool:
    source = item.source if hasattr(item, "source") else item.get("source")
    source_id = item.source_event_id if hasattr(item, "source_event_id") else item.get("source_event_id")
    age = item.age_at_exposure if hasattr(item, "age_at_exposure") else item.get("age_at_exposure")
    valid_ids = _event_ids(valid_event_ids)
    if source == "backstory":
        return source_id is None and age is None
    if source in ("experience", "intervention"):
        return source_id is not None and age is not None and (
            valid_ids is None or str(source_id) in valid_ids
        )
    return False


def protective_factor_has_provenance(item, valid_event_ids: Optional[Iterable[str]] = None) -> bool:
    source_id = item.source_event_id if hasattr(item, "source_event_id") else item.get("source_event_id")
    age = item.active_from_age if hasattr(item, "active_from_age") else item.get("active_from_age")
    valid_ids = _event_ids(valid_event_ids)
    # ProtectiveFactor predates an explicit source column. In the canonical
    # pipeline, null source_event_id is the existing backstory convention.
    if source_id is None:
        return age is None
    return age is not None and (valid_ids is None or str(source_id) in valid_ids)


def interpretation_has_provenance(item, valid_event_ids: Optional[Iterable[str]] = None) -> bool:
    source_id = item.source_event_id if hasattr(item, "source_event_id") else item.get("source_event_id")
    age = item.age_at_event if hasattr(item, "age_at_event") else item.get("age_at_event")
    valid_ids = _event_ids(valid_event_ids)
    if source_id is None:
        return age is None
    return age is not None and (valid_ids is None or str(source_id) in valid_ids)
