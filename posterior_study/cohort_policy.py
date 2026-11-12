"""Shared, explicit exclusion of summer/SMR course metadata and grade fields."""
from __future__ import annotations
import re
import pandas as pd

SUMMER_PATTERN=re.compile(r'(?<![A-Za-z])(?:SMR|SUMMER)(?![A-Za-z])',re.I)
METADATA_COLUMNS=('cohort','course_name','term','course_term')


def is_summer_label(value):
    return False if pd.isna(value) else bool(SUMMER_PATTERN.search(str(value)))


def exclude_summer_rows(frame,columns=METADATA_COLUMNS):
    """Use metadata only, never scan free text or numeric assignment scores.

    Any explicit summer metadata excludes the row even if another label conflicts.
    Unknown non-summer courses remain for the caller's mapping/schema validation.
    """
    fields=[c for c in columns if c in frame]
    if not fields:raise ValueError('Course/term metadata required for summer exclusion')
    mask=pd.Series(False,index=frame.index)
    labels={}
    for c in fields:
        matched=frame[c].map(is_summer_label)
        mask |= matched
        if matched.any():labels[c]=sorted(frame.loc[matched,c].astype(str).unique().tolist())
    audit=dict(policy='exclude SMR and summer course metadata; retain Fall/Winter/Spring only in study',
        metadata_fields=fields,input_rows=len(frame),excluded_summer_rows=int(mask.sum()),retained_rows=int((~mask).sum()),excluded_labels=labels)
    return frame.loc[~mask].copy(),audit


def require_non_summer_columns(columns):
    bad=[str(c) for c in columns if is_summer_label(c)]
    if bad:raise ValueError(f'Summer-labelled predictor/category columns are excluded: {bad}')
