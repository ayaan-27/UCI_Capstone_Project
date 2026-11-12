"""Build the RETRO/model follow-up, with weights/SMR audit when available, preserving the old deck."""
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit,ImageReader
from PIL import Image
from .analysis import ROOT

OUT=ROOT/'retro_followup_results';DEST=ROOT/'updated_presentation';DEST.mkdir(exist_ok=True)
W,H=13.333,7.5
BG='#F6F8FC';INK='#15273F';MUTED='#56677C';TEAL='#0F766E';PURPLE='#8050AD';ORANGE='#B45309';WHITE='#FFFFFF'
pdfmetrics.registerFont(TTFont('RF','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('RFB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
prs=Presentation();prs.slide_width=Inches(W);prs.slide_height=Inches(H)
pdf=canvas.Canvas(str(DEST/'MLC_RETRO_followup.pdf'),pagesize=(W*72,H*72))
notes=[]
def rgb(c):return tuple(int(c[i:i+2],16)/255 for i in (1,3,5))
class Slide:
 def __init__(self,title,sub,note):
  self.s=prs.slides.add_slide(prs.slide_layouts[6]);self.s.background.fill.solid();self.s.background.fill.fore_color.rgb=RGBColor.from_string(BG[1:])
  pdf.setFillColorRGB(*rgb(BG));pdf.rect(0,0,W*72,H*72,stroke=0,fill=1)
  self.text(.65,.45,12,.35,f'RETRO FOLLOW-UP  /  {len(prs.slides):02}',11,TEAL,True)
  self.text(.65,1.05,12,.7,title,27,INK,True);self.text(.67,1.85,12,.5,sub,12,MUTED)
  self.note=note;self.title=title
 def text(self,x,y,w,h,text,size=16,c=INK,bold=False):
  font='RFB' if bold else 'RF'
  while True:
   lines=[]
   for line in str(text).split('\n'):lines.extend(simpleSplit(line,font,size,w*72-3) if line else [''])
   leading=size*1.25
   if len(lines)*leading<=h*72 or size<=9:break
   size-=.5
  tf=self.s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame
  tf.clear();tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
  for i,line in enumerate(lines):
   p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(c[1:]);p.space_after=Pt(0);p.line_spacing=Pt(leading)
   pdf.setFont(font,size);pdf.setFillColorRGB(*rgb(c));pdf.drawString(x*72,(H-y)*72-size-i*leading,line)
 def rect(self,x,y,w,h,c=WHITE):
  shape=self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(c[1:]);shape.line.fill.background()
  pdf.setFillColorRGB(*rgb(c));pdf.roundRect(x*72,(H-y-h)*72,w*72,h*72,8,stroke=0,fill=1)
 def image(self,p,x,y,w,h):
  iw,ih=Image.open(p).size;s=min(w/iw,h/ih);dw,dh=iw*s,ih*s;x+=(w-dw)/2;y+=(h-dh)/2
  self.s.shapes.add_picture(str(p),Inches(x),Inches(y),Inches(dw),Inches(dh));pdf.drawImage(ImageReader(str(p)),x*72,(H-y-dh)*72,dw*72,dh*72)
 def table(self,headers,rows,widths,y=2.6,rowh=.58):
  for j,row in enumerate([headers]+rows):
   x=.7
   for value,w in zip(row,widths):
    self.rect(x,y+j*rowh,w,rowh-.02,INK if j==0 else WHITE);self.text(x+.13,y+j*rowh+.1,w-.25,rowh-.15,value,13,WHITE if j==0 else INK,j==0);x+=w
 def finish(self):
  self.text(.7,7.1,12,.25,'MY LEARNING COACH  /  EXPLORATORY FINDINGS  /  PRIOR PRESENTATION RETAINED',8,MUTED)
  self.s.notes_slide.notes_text_frame.text=self.note;notes.append((self.title,self.note));pdf.showPage()

s=Slide('We estimated associations, not causal effects','Conditional Block B posterior: final-percentage points per one training standard deviation.',
'''Professor, we can now quantify conditional associations and test prediction improvements, but these are not causal effects. Wellness has a mean association of about plus 0.20 points per training standard deviation, with an interval from minus 0.39 to plus 0.78. All of the displayed intervals include zero. These estimates hold grades and the other inputs fixed, depend on the shrinkage prior and imputation, and are not effects per one questionnaire rating point. Conditioning on grades may also block some pathways through which early motivation relates to the final result. A posterior sign probability cannot by itself establish either a causal effect or improved forecasting.''')
c=pd.read_csv(ROOT/'posterior_results/coefficient_posteriors.csv').head(6)
names={'log_page_views':'LMS page views','log_lms_participations':'LMS participations','cost_support':'EVC source cost/support','expectancy':'EVC expectancy','value':'EVC value','wellness':'Wellness'}
s.table(['Input','Mean association','95% credible interval'],[[names[r.feature],f'{r.mean_points_per_SD:+.2f}',f'[{r.lower95:+.2f}, {r.upper95:+.2f}]'] for r in c.itertuples()],[5.4,2.8,3.75],y=2.45)
s.text(.85,6.65,11.5,.3,'These estimates do not tell us what would happen if we intervened to improve wellness.',12,ORANGE,True);s.finish()

s=Slide('The uploaded RETRO is a distinct text source','870 response rows; 74 students; three prompts across Weeks 2, 4, 6, 8 and 10.',
'''I have now incorporated the newly supplied RETRO export. It contains open reflections about what went well, what did not go well, and what could improve motivation and engagement. This is different from the numerical early EVC features already in the original model. All IDs match the existing grade table. I restrict the initial comparison to Week 2 and Week 4 responses, giving 68 early respondents across the three covered terms. There are no exact submission timestamps, so I cannot yet claim verified end-of-week-four availability. Later weeks are deliberately excluded. Two later-term evaluations are possible, with only 20 then 60 training students. That is a very small basis for learning from text.''')
s.table(['Term','Students in grade table','Week 2/4 respondents'],[['Fall 2025','20','13'],['Winter 2026','40','25'],['Spring 2026','43','30']],[4.0,4.0,3.95],y=2.7)
s.rect(.75,5.35,11.85,.95,'#FFF1DE');s.text(.95,5.55,11.4,.6,'No exact timestamps. Weeks 6/8/10 are excluded. Earlier three terms did not have this instrument.',17,ORANGE,True);s.finish()

s=Slide('RETRO content has not shown a consistent gain','Larger grades-only baseline; Week 2/4 text; two later-term checks; Ridge alpha 10.',
'''I compare grades alone with grades plus response measures, and then grades plus words and the same response measures. The response measures include whether a student responded, how often and how much they wrote. The text model improves error by about 0.31 points in Winter but worsens it by 0.04 in Spring. Across these two terms, response measures alone improve more than words plus response measures. The words therefore do not show a consistent added benefit in this scenario. This does not mean the reflections are uninformative: a small TF-IDF model and two terms are limited. It means I cannot yet give a reliable numerical effect for RETRO as a factor. These results use different training windows from the previous four-term analysis.''')
s.image(OUT/'retro_gains.png',.7,2.4,8.8,3.95)
s.rect(9.75,2.9,2.8,2.7,WHITE);s.text(9.95,3.1,2.4,2.3,'Separate the words from who responds.\n\nNo consistent independent text benefit established.',17,PURPLE,True)
s.text(.85,6.5,11.5,.3,'Positive = less error. Fixed text baseline; prior/regularization sensitivities are in the result tables.',11,MUTED);s.finish()

s=Slide('A bigger model did not improve the grade-based forecast','Same four later-term numeric checks; fixed candidate settings; lower MAE is better.',
'''I tested robust regression and two restrained tree methods rather than assuming they would improve on the Bayesian model. The larger-grade Bayesian and Ridge baseline has average error 2.95 points. Huber gives 3.45, ExtraTrees 4.27 and histogram boosting 4.32. The Bayesian model and Ridge have the same point predictions under the same penalty; they are not independent discoveries. Some alternatives slightly help the full no-grades model, but the previous LMS-only Bayesian model is still a stronger simple comparison. These are explored fixed-setting benchmarks, not exhaustive tuning or a claim of the best possible model. The point-error comparison does not establish superior calibration for the alternatives.''')
s.image(OUT/'model_comparison.png',.7,2.4,9.0,4.0)
s.rect(10,3.0,2.55,2.35,WHITE);s.text(10.2,3.25,2.15,1.85,'Keep the simple baseline.\n\nImprove the problem definition before adding complexity.',17,TEAL,True);s.finish()

s=Slide('Improve temporal structure and measurement first','A candidate longitudinal design—not a newly fitted or causally identified DAG.',
'''I would improve the DAG by fixing one forecast time, then unrolling feedback through time. A mark can change a later motivation rating or reflection, and these may help predict subsequent activity and future marks. I would not automatically treat a reflection as the cause of a difficulty it describes. A cleaner target may be performance on remaining coursework, combined with already earned marks using known weights. I would validate survey scoring and human-coded RETRO themes, account for observed prior preparation and term context, and examine response selection. A regularized hierarchical Bayesian model with robust residuals is a reasonable candidate after longitudinal inputs are available, but is not fitted here and may not improve accuracy. These six terms still support an honest exploratory capstone.''')
for x,t,b,col in [(.8,'Earlier marks','Observed performance\nat time t',TEAL),(4.95,'Later EVC / RETRO','Response to prior experience\nat time t+1',PURPLE),(9.1,'Future work','Activity and new marks\nat time t+2',INK)]:
 s.rect(x,2.65,3.4,1.55,col);s.text(x+.2,2.85,3,.45,t,19,WHITE,True);s.text(x+.2,3.4,3,.6,b,13,WHITE)
s.text(4.3,3.2,.55,.5,'→',24,MUTED,True);s.text(8.45,3.2,.55,.5,'→',24,MUTED,True)
s.text(.95,4.7,11.5,1.65,'1  Verify grade release/revision dates and survey submission times.\n2  Validate questionnaire scoring and coded RETRO themes.\n3  Compare prediction of remaining coursework at the same checkpoint.\n4  Test partial pooling, robust residuals and missing-data models against the simple baseline.',17,INK)
s.finish()

if (ROOT/'grading_results/category_weights.csv').exists():
 s=Slide('Confirmed category weights: 100% main grade',
  'The user confirmed the same weights across all six historical non-summer terms.',
  'The supplied workbook resolves the category-weight question. Written Mastery I is 20 percent, Written Mastery II is 35 percent, both verbal categories are 10 percent, teamwork is 10 percent, growth mindset is 10 percent, and resilience and agency are 5 percent. The main grade totals 100 percent. Surveys and team-manager extra credit can add 0.75 and 0.25 points respectively; the MLC extra-credit group has zero weight here. I do not renormalize all weights to 101 percent. These are grading rules, not estimated effects of wellness or motivation. The workbook contains published and unpublished versions, so I still need each historical term’s effective assignment denominator rather than transferring current inventory totals.')
 weights=pd.read_csv(ROOT/'grading_results/category_weights.csv')
 main=weights[~weights.is_extra_credit]
 s.table(['Main grading category','Course weight'],[[r.category,f'{100*r.weight:g}%'] for r in main.itertuples()],[9.0,2.95],y=2.45,rowh=.47)
 s.text(.85,6.4,11.5,.55,'Extra credit: Surveys +0.75 points; Team Manager +0.25 points; My Learning Coach 0 points.',13,TEAL,True)
 s.finish()
 s=Slide('Separate earned marks from remaining performance',
  'Remaining-work accounting is implemented and tested; historical remaining-work outcomes are not yet reconstructed.',
  'The improved target separates already earned grade points from uncertain future performance. A final total equals the known contribution plus remaining course weight times the remaining main-work percentage, plus extra credit. This accounting is now implemented and tested with actual availability cutoffs, with summer courses excluded. The current data already contain 191 non-summer students and none is removed. The old manifest has 168 SMR-labelled aggregate entries, but none was used as a predictor. No previous numerical result changes just because the exclusion is explicit. To fit a real remaining-work model I still need the complete historical grade exports and effective assignment catalogs, including extra credit and release or revision snapshots. The supplied workbook has Fall 2026 due dates; deadlines are not historical grade-release timestamps.')
 s.rect(.75,2.55,11.85,1.5,WHITE)
 s.text(1.0,2.8,11.35,1.0,'Final total = known earned contribution\n+ (1 − known course weight) × remaining main-work percentage\n+ extra credit',19,TEAL,True)
 s.text(.9,4.55,11.6,.65,'SMR/Summer is explicitly excluded. Current cohort: 191 students, all Fall/Winter/Spring.',17,INK,True)
 s.text(.9,5.55,11.6,1.0,'Next required data: complete historical grade exports, effective assignment denominators, extra credit, and actual score-availability history.',16,ORANGE,True)
 s.finish()

prs.save(DEST/'MLC_RETRO_followup.pptx');pdf.save()
(DEST/'MLC_RETRO_followup_notes.md').write_text('# RETRO follow-up speaker notes\n\n'+'\n\n'.join(f'## {i}. {t}\n\n{n}' for i,(t,n) in enumerate(notes,1)))
print(f'Saved {len(prs.slides)}-slide RETRO/weights addendum, PDF, and notes')
