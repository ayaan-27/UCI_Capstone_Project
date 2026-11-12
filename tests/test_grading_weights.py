"""Summer exclusion, actual-cutoff accounting and exact weighted recombination."""
import unittest
import numpy as np
import pandas as pd
from posterior_study.cohort_policy import exclude_summer_rows,require_non_summer_columns
from posterior_study.grading_weights import known_contributions,remaining_target,combine_final
from posterior_study.retro_followup import load_retro
import tempfile
from pathlib import Path

class GradingTests(unittest.TestCase):
    def setUp(self):
        self.cat=pd.DataFrame({'course_id':['1']*3,'cohort':['2025 FAL']*3,'assignment_id':['a','b','c'],
            'category':['Writing','Writing','Other'],'points_possible':[40.,60.,100.]})
        self.students=pd.DataFrame({'course_id':['1']*2,'cohort':['2025 FAL']*2,'student_id':['s1','s2']})
        self.snap=pd.DataFrame({'course_id':['1']*3,'cohort':['2025 FAL']*3,'student_id':['s1']*3,
            'assignment_id':['a','b','a'],'score':[30.,60.,40.],
            'available_at':['2025-10-01T12:00:00-07:00','2025-11-01T12:00:00-07:00','2025-11-02T12:00:00-08:00']})
        self.weights={'Writing':.2,'Other':.8};self.cut='2025-10-15T23:59:00-07:00'

    def test_summer_metadata_and_fields_excluded_without_reading_free_text(self):
        frame=pd.DataFrame({'cohort':['2025 FAL','2026_SMR','2026 SMR2','2026 SPR'],
            'term':['Fall','Summer','SMR','Summer'],'text':['summer internship','a','b','a']})
        kept,audit=exclude_summer_rows(frame)
        self.assertEqual(len(kept),1);self.assertEqual(kept.iloc[0].cohort,'2025 FAL')
        self.assertEqual(audit['excluded_summer_rows'],3)
        with self.assertRaisesRegex(ValueError,'Summer-labelled'):require_non_summer_columns(['Written Mastery - SMR Final Score'])

    def test_category_weighting_is_not_global_points_and_future_scores_do_not_leak(self):
        got=known_contributions(self.cat,self.snap,self.students,self.weights,self.cut).set_index('student_id')
        # 20% category * 30 / 100 category points = 6 final percentage points.
        self.assertAlmostEqual(got.loc['s1','known_contribution_points'],6.)
        self.assertAlmostEqual(got.loc['s1','known_course_fraction'],.08)
        self.assertEqual(got.loc['s2','known_course_fraction'],0)
        future=self.snap.copy();future.loc[future.assignment_id.eq('b'),'score']=0
        changed=known_contributions(self.cat,future,self.students,self.weights,self.cut).set_index('student_id')
        pd.testing.assert_frame_equal(got,changed)

    def test_remaining_target_roundtrip_keeps_extra_credit_separate(self):
        # 80 main-grade points + 0.75 bonus, 6 points already earned, 8% known.
        rem=remaining_target(80.75,.75,6.,.08)
        self.assertAlmostEqual(float(rem),74/.92)
        self.assertAlmostEqual(float(combine_final(6.,.08,rem,.75)),80.75)
        with self.assertRaisesRegex(ValueError,'positive remaining'):remaining_target(80.,0.,80.,1.)

    def test_later_blank_revokes_a_previously_known_grade(self):
        blank=self.snap.iloc[:1].copy();blank['available_at']='2025-10-10T00:00:00-07:00';blank['score']=np.nan
        result=known_contributions(self.cat,pd.concat([self.snap,blank]),self.students,self.weights,self.cut)
        self.assertEqual(result.known_assignments.sum(),0)

    def test_unverified_time_and_incomplete_category_roster_rejected(self):
        with self.assertRaisesRegex(ValueError,'timezone'):
            known_contributions(self.cat,self.snap,self.students,self.weights,'2025-10-15')
        with self.assertRaisesRegex(ValueError,'every main category'):
            known_contributions(self.cat.iloc[:2],self.snap,self.students,self.weights,self.cut)

    def test_summer_retro_course_skipped_before_unknown_course_validation(self):
        base=pd.DataFrame({'cohort':['2025 FAL'],'student_id':['MLCStudent1']})
        raw=pd.DataFrame({'lms_course_id':[76548,99999],'student_name':['MLCStudent1','MLCStudent2'],
            'user_id':['MLCStudent1','MLCStudent2'],'lms_user_id':['MLCStudent1','MLCStudent2'],
            'course_name':['2025 FAL ENGR190W','2026 SMR ENGR190W'],'term':['Fall','Summer'],
            'week':['Week 2','Week 2'],'retrospective_q':['What went well? test']*2,'response':['helpful feedback','summer text']})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'retro.csv';raw.to_csv(p,index=False)
            features,_,filtered=load_retro(p,base)
        self.assertEqual(len(filtered),1)
        self.assertEqual(filtered.attrs['summer_exclusion']['excluded_summer_rows'],1)
        self.assertNotIn('summer',features.text_went_well.iloc[0])

if __name__=='__main__':unittest.main()
