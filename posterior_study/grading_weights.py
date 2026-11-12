"""Extract weight evidence and compute fixed-rule remaining-work components.

The uploaded inventory is not silently treated as an effective historical
assignment roster. Published/all-item denominators are scenarios, not verified
Canvas grading rules. Due dates are never used as grade-availability timestamps.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from .analysis import ROOT, TERMS
from .cohort_policy import exclude_summer_rows,is_summer_label

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def read_inventory(path):
    """Read cached scalar cells of the named sheet with the standard library.

    Verify subtotals independently against item rows rather than recalculating
    arbitrary Excel formula text or executing anything in the attachment.
    """
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(e.text or '' for e in si.findall('.//m:t',NS))
                     for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        book=ET.fromstring(z.read('xl/workbook.xml'))
        sheets=[s for s in book.findall('m:sheets/m:sheet',NS) if s.attrib['name']=='Assignments by category']
        if len(sheets)!=1:raise ValueError('Expected one Assignments by category sheet')
        relid=sheets[0].attrib['{'+NS['r']+'}id']
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rel=next(r for r in rels if r.attrib['Id']==relid)
        if rel.attrib.get('TargetMode')=='External':raise ValueError('External worksheet not supported')
        target=rel.attrib['Target'];sheet=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        rows=[]
        for row in ET.fromstring(z.read(sheet)).findall('m:sheetData/m:row',NS):
            d={}
            for c in row.findall('m:c',NS):
                letter=re.sub(r'\d','',c.attrib['r']);v=c.find('m:v',NS)
                raw=v.text if v is not None and v.text is not None else ''
                if c.attrib.get('t')=='s':value=strings[int(raw)]
                elif c.attrib.get('t')=='inlineStr':value=''.join(t.text or '' for t in c.findall('.//m:t',NS))
                else:value=raw
                d[letter]=value
            d['row']=int(row.attrib['r']);rows.append(d)
    summary=[];assignments=[];current=None;exclusions=[];source_url=None
    in_summary=False
    for r in rows:
        name=r.get('B','')
        if name.startswith('Source: '):source_url=name[8:]
        if name=='Category' and r.get('C')=='Course weight':in_summary=True;continue
        if in_summary:
            if name=='All categories':in_summary=False;continue
            if name and r.get('C'):
                if is_summer_label(name):exclusions.append({'row':r['row'],'label':name});continue
                summary.append(dict(category=name,weight=float(r['C']),catalog_points_all=float(r['D']),assignment_count=int(r['E']),
                    is_extra_credit=name.startswith('Extra Credit:'),source_row=r['row']))
        if r.get('D')=='Course weight':current=name
        aid=r.get('I','')
        if aid and r.get('H','').startswith('https://'):
            if current is None:raise ValueError('Assignment has no category')
            if is_summer_label(current) or is_summer_label(name):
                exclusions.append({'row':r['row'],'label':name});continue
            url=r['H'];match=re.search(r'/courses/(\d+)/assignments/(\d+)',url)
            if match is None or match.group(2)!=aid:raise ValueError('Assignment ID/URL mismatch')
            if r.get('D') not in ['Yes','No']:raise ValueError('Unknown publication status')
            points=float(r['C'])
            if points<0 or not np.isfinite(points):raise ValueError('Invalid points')
            assignments.append(dict(course_id=match.group(1),assignment_id=aid,category=current,assignment=name,
                points_possible=points,published=r['D']=='Yes',due_date=r.get('E',''),due_time=r.get('F',''),
                due_timezone='America/Los_Angeles',assignment_url=url,source_row=r['row']))
    weights=pd.DataFrame(summary);items=pd.DataFrame(assignments)
    if items.assignment_id.duplicated().any():raise ValueError('Duplicate assignment ID')
    if set(items.category)!=set(weights.category):raise ValueError('Category summaries and details disagree')
    actual=items.groupby('category').points_possible.agg(['sum','size'])
    for r in weights.itertuples():
        if not np.isclose(actual.loc[r.category,'sum'],r.catalog_points_all) or actual.loc[r.category,'size']!=r.assignment_count:
            raise ValueError(f'Cached category totals disagree with item rows: {r.category}')
    if not np.isclose(weights.loc[~weights.is_extra_credit,'weight'].sum(),1):raise ValueError('Main weights must total 100%')
    weights['catalog_points_published']=weights.category.map(items[items.published].groupby('category').points_possible.sum()).fillna(0)
    weights['published_assignment_count']=weights.category.map(items[items.published].groupby('category').size()).fillna(0).astype(int)
    items=items.merge(weights[['category','weight','is_extra_credit','catalog_points_all','catalog_points_published']],on='category',validate='many_to_one')
    items['all_inventory_course_fraction']=items.weight*items.points_possible/items.catalog_points_all
    # This is an explicitly labelled publication-only scenario, not an official
    # effective denominator. Unpublished duplicate versions require verification.
    den=items.catalog_points_published.replace(0,np.nan)
    items['published_scenario_course_fraction']=np.where(items.published,items.weight*items.points_possible/den,0.)
    metadata=dict(source_url=source_url,course_ids=sorted(items.course_id.unique().tolist()),
        sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),excluded_summer_inventory_rows=exclusions,
        main_weight_sum=float(weights.loc[~weights.is_extra_credit,'weight'].sum()),
        extra_credit_weight_sum=float(weights.loc[weights.is_extra_credit,'weight'].sum()),
        category_scope='same category weights confirmed by user for six non-summer historical terms',
        confirmed_historical_terms=TERMS,assignment_scope='inventory/dates for course 84595 only; historical denominators/versions unverified',
        due_dates_are_release_dates=False,summer_policy='exclude summer/SMR courses and summer-tagged categories/fields')
    return weights,items,metadata


def _utc(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:raise ValueError('Availability times/cutoff must include timezone')
    return t.tz_convert('UTC')


def known_contributions(effective_catalog,snapshots,students,main_weights,cutoff):
    """Compute earned contribution and known course weight at an actual cutoff.

    Catalog must be the EFFECTIVE main-assignment roster for each course with
    fixed point denominators, no dropped/excused student-specific adjustments.
    The inventory exported by read_inventory is not automatically this roster.
    snapshots must hold historical scores with actual available_at, not due dates
    or final-export scores backdated to assignment deadlines. students preserves
    people with no released scores. Extra credit is separate.
    """
    if not np.isclose(sum(main_weights.values()),1) or any(w<0 for w in main_weights.values()):raise ValueError('Main category weights must total 1')
    if any(is_summer_label(k) for k in main_weights):raise ValueError('Summer category weights excluded')
    cat,_=exclude_summer_rows(effective_catalog);ss,_=exclude_summer_rows(snapshots);roster,_=exclude_summer_rows(students)
    key=['course_id','cohort','assignment_id'];who=['student_id','course_id','cohort']
    for c in key+['category','points_possible']:
        if c not in cat:raise ValueError(f'Missing effective catalog field {c}')
    for c in who+['assignment_id','score','available_at']:
        if c not in ss:raise ValueError(f'Missing score snapshot field {c}')
    for c in who:
        if c not in roster:raise ValueError(f'Missing student roster field {c}')
    for df in [cat,ss,roster]:
        for c in ['course_id','assignment_id']:
            if c in df:df[c]=df[c].astype(str)
    if cat.duplicated(key).any() or roster.duplicated(who).any():raise ValueError('Duplicate catalog/roster keys')
    if cat.empty or roster.empty:raise ValueError('No eligible non-summer catalog/students')
    coursekeys=['course_id','cohort']
    if not roster[coursekeys].drop_duplicates().merge(cat[coursekeys].drop_duplicates(),on=coursekeys,how='left',indicator=True)._merge.eq('both').all():raise ValueError('Student course has no effective catalog')
    if cat.category.map(is_summer_label).any():raise ValueError('Summer categories excluded')
    if not np.isfinite(cat.points_possible).all() or (cat.points_possible<=0).any():raise ValueError('Effective assignment points must be positive')
    for _,d in cat.groupby(['course_id','cohort']):
        if set(d.category)!=set(main_weights):raise ValueError('Effective catalog must cover every main category')
    if any(c in ss and ss[c].fillna(False).any() for c in ['excused','dropped']):raise ValueError('Student-specific grade exclusions need effective per-student denominators')
    cut=_utc(cutoff)
    ss['available_at']=ss.available_at.map(_utc)
    if ss.duplicated(who+['assignment_id','available_at']).any():raise ValueError('Ambiguous same-time score snapshots')
    # Keep the latest state BEFORE filtering blank scores: a later blank can
    # revoke an earlier grade, so it must not revive the older score.
    latest=ss[ss.available_at.le(cut)].sort_values('available_at').drop_duplicates(who+['assignment_id'],keep='last')
    valid=latest[latest.score.notna()].copy()
    if not np.isfinite(valid.score).all() or (valid.score<0).any():raise ValueError('Invalid released score')
    totals=cat.groupby(['course_id','cohort','category']).points_possible.transform('sum')
    cat['course_fraction']=cat.category.map(main_weights)*cat.points_possible/totals
    merged=valid.merge(cat,on=key,how='left',validate='many_to_one',indicator=True)
    if not merged._merge.eq('both').all():raise ValueError('Snapshot assignment not in effective main catalog')
    if not valid.merge(roster,on=who,how='left',indicator=True)._merge.eq('both').all():raise ValueError('Snapshot student not in roster')
    merged['known_points']=100*merged.course_fraction*merged.score/merged.points_possible
    summary=merged.groupby(who).agg(known_course_fraction=('course_fraction','sum'),known_contribution_points=('known_points','sum'),known_assignments=('assignment_id','size')).reset_index()
    result=roster.merge(summary,on=who,how='left',validate='one_to_one')
    for col in ['known_course_fraction','known_contribution_points','known_assignments']:result[col]=result[col].fillna(0)
    result['remaining_course_fraction']=1-result.known_course_fraction
    if (result.remaining_course_fraction< -1e-9).any():raise ValueError('Known course weight exceeds main total')
    return result


def remaining_target(final_total_percentage,extra_credit_contribution_points,known_contribution_points,known_course_fraction):
    """Normalized remaining-main-work percentage under fixed verified rules.

    Explicit extra-credit contribution is required; do not silently assume zero.
    Requires an uncapped final total with no unmodelled grading adjustments.
    May legitimately lie outside [0,100]; no clipping hides accounting mismatch.
    """
    final,extra,known,weight=np.broadcast_arrays(*[np.asarray(x,dtype=float) for x in [final_total_percentage,extra_credit_contribution_points,known_contribution_points,known_course_fraction]])
    if not all(np.isfinite(x).all() for x in [final,extra,known,weight]):raise ValueError('All target accounting inputs must be known and finite')
    if (weight<0).any() or (weight>=1).any():raise ValueError('Need a positive remaining course fraction')
    return (final-extra-known)/(1-weight)


def combine_final(known_contribution_points,known_course_fraction,remaining_main_percentage,extra_credit_contribution_points):
    known,weight,rem,extra=np.broadcast_arrays(*[np.asarray(x,dtype=float) for x in [known_contribution_points,known_course_fraction,remaining_main_percentage,extra_credit_contribution_points]])
    if not all(np.isfinite(x).all() for x in [known,weight,rem,extra]) or (weight<0).any() or (weight>1).any():raise ValueError('Invalid weighted components')
    return known+(1-weight)*rem+extra


def audit(path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    weights,items,meta=read_inventory(path)
    weights.to_csv(out/'category_weights.csv',index=False);items.to_csv(out/'assignment_inventory.csv',index=False)
    frame,a=exclude_summer_rows(pd.read_csv(ROOT/'mlc_results/expanded_student_features.csv'))
    manifest=pd.read_csv(ROOT/'mlc_results/all_column_eligibility_manifest.csv')
    sm=manifest.source_column.map(is_summer_label)
    used=manifest.loc[sm,['in_block_a','in_block_b']].any(axis=1)
    if used.any():raise ValueError('Earlier model used summer-labelled columns; refit required')
    meta['current_cohort_audit']=a;meta['summer_labelled_manifest_rows']=int(sm.sum());meta['summer_labelled_predictors_used']=int(used.sum())
    meta['retained_cohort_counts']=frame.groupby('cohort').size().to_dict()
    # Exact-name mapping is an audit only. Do not guess renamed equivalents or
    # reconstruct cross-category pooled grades from a single stored percentage.
    sources=pd.read_csv(ROOT/'mlc_results/selected_assessment_sources.csv')
    def canonical(name):return re.sub(r'\s+',' ',re.sub(r'\s*\(\d+\)\s*$','',str(name))).strip()
    sources['name_key']=sources.source_column.map(canonical);inv=items.copy();inv['name_key']=inv.assignment.map(canonical)
    match=sources.merge(inv[['name_key','category','points_possible','published','assignment_id']],on='name_key',how='left',validate='many_to_one',suffixes=('_historical','_84595'))
    match['same_points']=np.isclose(match.points_possible_historical,match.points_possible_84595,equal_nan=False)
    match['mapping_status']=np.where(match.assignment_id.isna(),'no exact title match',np.where(~match.same_points,'point maximum differs',np.where(~match.published.eq(True),'matched item is unpublished in 84595','title/points match; historical category denominator still unverified')))
    match.to_csv(out/'historical_assignment_mapping_audit.csv',index=False)
    meta['historical_mapping_status_counts']=match.mapping_status.value_counts().to_dict()
    cfg=dict(main_category_weights=dict(zip(weights.loc[~weights.is_extra_credit,'category'],weights.loc[~weights.is_extra_credit,'weight'])),
        extra_credit_weights=dict(zip(weights.loc[weights.is_extra_credit,'category'],weights.loc[weights.is_extra_credit,'weight'])),
        weight_confirmation='user confirmed same weights for six historical non-summer terms',
        applicable_historical_terms=TERMS,excluded_terms=['SMR','Summer'],inventory_course_ids=meta['course_ids'],
        historical_assignment_denominators_verified=False,historical_grade_release_times_verified=False,
        extra_credit_not_renormalized_into_main=True)
    (out/'grading_config.json').write_text(json.dumps(cfg,indent=2))
    (out/'weight_audit.json').write_text(json.dumps(meta,indent=2))
    print(weights[['category','weight','catalog_points_all','catalog_points_published']].to_string(index=False))
    print('Summer audit:',a,'; unused summer-labelled manifest rows:',int(sm.sum()))
    return meta

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--weights-xlsx',type=Path,required=True);ap.add_argument('--output',type=Path,default=ROOT/'grading_results')
    args=ap.parse_args();audit(args.weights_xlsx,args.output)
