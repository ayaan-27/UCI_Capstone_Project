"""Rebuild editable PPTX and matching vector PDF from the executed study.

python -m pip install -r posterior_study/requirements-presentation.txt
python -m posterior_study.build_presentation
"""
from pathlib import Path
from io import BytesIO
import json
import textwrap
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit, ImageReader
from .analysis import ROOT

OUT=ROOT/'posterior_results'
DEST=ROOT/'updated_presentation';DEST.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',FONT));pdfmetrics.registerFont(TTFont('DVB',BOLD))
BG='#F6F8FC';NAVY='#15273F';MUTED='#56677C';TEAL='#0F766E';BLUE='#2563EB';PURPLE='#8050AD';ORANGE='#B45309';WHITE='#FFFFFF';BORDER='#DCE3ED'
W,H=13.333333,7.5
prs=Presentation();prs.slide_width=Inches(W);prs.slide_height=Inches(H)
pdf=canvas.Canvas(str(DEST/'MLC_posterior_updated.pdf'),pagesize=(W*72,H*72))
pdf.setTitle('My Learning Coach — posterior simulation and predictive value')
notes=[]


def color(c):return RGBColor.from_string(c.lstrip('#'))
def pdfcolor(c):return tuple(int(c[i:i+2],16)/255 for i in (1,3,5))

class Slide:
 def __init__(self,tag,title,subtitle,note):
  self.s=prs.slides.add_slide(prs.slide_layouts[6]);self.s.background.fill.solid();self.s.background.fill.fore_color.rgb=color(BG)
  pdf.setFillColorRGB(*pdfcolor(BG));pdf.rect(0,0,W*72,H*72,fill=1,stroke=0)
  self.rect(.5,.47,.12,.3,TEAL)
  self.text(.8,.46,12,.35,tag.upper(),11,TEAL,True)
  self.text(.65,1.02,12.05,.72,title,27,NAVY,True)
  self.text(.67,1.78,12,.6,subtitle,12,MUTED)
  self.note=note;self.title=title
 def rect(self,x,y,w,h,fill=WHITE,stroke=None,radius=False):
  s=self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x),Inches(y),Inches(w),Inches(h))
  s.fill.solid();s.fill.fore_color.rgb=color(fill)
  s.line.fill.background() if stroke is None else None
  if stroke:s.line.color.rgb=color(stroke);s.line.width=Pt(.8)
  pdf.setFillColorRGB(*pdfcolor(fill));pdf.setStrokeColorRGB(*pdfcolor(stroke or fill));pdf.setLineWidth(.8)
  if radius:pdf.roundRect(x*72,(H-y-h)*72,w*72,h*72,8,fill=1,stroke=int(bool(stroke)))
  else:pdf.rect(x*72,(H-y-h)*72,w*72,h*72,fill=1,stroke=int(bool(stroke)))
 def text(self,x,y,w,h,txt,size=16,c=NAVY,bold=False):
  face='DVB' if bold else 'DV'
  # Common wrapping and line breaks keep PDF and PowerPoint consistent.
  while True:
   lines=[]
   for p in str(txt).split('\n'):
    lines.extend(simpleSplit(p,face,size,w*72-3) if p else [''])
   leading=size*1.25
   if len(lines)*leading<=h*72+1 or size<=8:break
   size-=.5
  box=self.s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame
  tf.clear();tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=False
  for i,line in enumerate(lines):
   p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color(c);p.space_after=Pt(0);p.space_before=Pt(0);p.line_spacing=Pt(leading)
   pdf.setFillColorRGB(*pdfcolor(c));pdf.setFont(face,size);pdf.drawString(x*72,(H-y)*72-size-i*leading,line)
 def line(self,x1,y1,x2,y2,c=MUTED):
  from pptx.enum.shapes import MSO_CONNECTOR
  s=self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1),Inches(y1),Inches(x2),Inches(y2));s.line.color.rgb=color(c);s.line.width=Pt(1.5)
  pdf.setStrokeColorRGB(*pdfcolor(c));pdf.setLineWidth(1.5);pdf.line(x1*72,(H-y1)*72,x2*72,(H-y2)*72)
 def image(self,path,x,y,w,h):
  iw,ih=Image.open(path).size;ratio=min(w/iw,h/ih);dw,dh=iw*ratio,ih*ratio
  x+=(w-dw)/2;y+=(h-dh)/2
  self.s.shapes.add_picture(str(path), Inches(x),Inches(y),width=Inches(dw),height=Inches(dh))
  pdf.drawImage(ImageReader(str(path)),x*72,(H-y-dh)*72,dw*72,dh*72)
 def card(self,x,y,w,h,title,body,c=TEAL):
  self.rect(x,y,w,h,WHITE,BORDER,True);self.text(x+.2,y+.2,w-.4,.55,title,19,c,True);self.text(x+.2,y+.8,w-.4,h-.95,body,15,NAVY)
 def table(self,headers,rows,widths,y=2.55,rowh=.57,size=14):
  x=.7
  for header,w in zip(headers,widths):
   self.rect(x,y,w,rowh,NAVY);self.text(x+.12,y+.12,w-.2,rowh-.16,header,12,WHITE,True);x+=w
  for i,row in enumerate(rows):
   x=.7
   for v,w in zip(row,widths):
    self.rect(x,y+(i+1)*rowh,w,rowh,WHITE if i%2==0 else '#EAF0F8');self.text(x+.12,y+(i+1)*rowh+.13,w-.2,rowh-.16,str(v),size,NAVY);x+=w
 def finish(self):
  self.line(.65,7.0,12.7,7.0,BORDER)
  self.text(.68,7.12,10,.2,'MY LEARNING COACH  /  UCI CAPSTONE  /  EXPLORATORY RETROSPECTIVE STUDY',8,MUTED)
  self.text(12,7.09,.6,.25,f'{len(prs.slides):02}',10,TEAL,True)
  self.s.notes_slide.notes_text_frame.text=self.note
  notes.append((self.title,self.note));pdf.showPage()

prov=json.loads((OUT/'provenance.json').read_text());checks=prov['simulation_checks']
macro=pd.read_csv(OUT/'macro_metrics.csv');gains=pd.read_csv(OUT/'paired_gain_summary.csv');coef=pd.read_csv(OUT/'coefficient_posteriors.csv')

s=Slide('01 / The question','Do the extra data improve our predictions?',
 'Updated analysis: posterior simulation + source-by-source tests on the six existing terms.',
 '''Professor, I have now separated two questions that were mixed together in the earlier presentation. First, what relationships and future outcomes does my Bayesian model consider plausible? Second, does adding a source of data actually improve predictions for later students? I implemented posterior sampling and a real MCMC check for the first question, and compared models on the same later students for the second. The central finding is that the extra data did not improve average error beyond the larger grade bundle. This is an exploratory result from existing classes, not proof that motivation or wellness is unimportant. The original notebook and original results remain available.''')
s.card(.7,2.65,7.7,2.65,'What I tested','Grades alone, then LMS activity, EVC, wellness, every combination, and each source removed from the full model.')
s.rect(8.65,2.65,3.95,2.65,NAVY,radius=True);s.text(8.9,2.95,3.4,.55,'Main finding',17,'#71E0CA',True)
s.text(8.9,3.7,3.4,1.25,'No added average-error benefit beyond grades shown.',25,WHITE,True)
s.text(.85,5.85,11.5,.6,'Simulation helps describe uncertainty. Later-term comparisons test predictive value.',19,TEAL,True);s.finish()

s=Slide('02 / What data are actually available','191 students, six terms, four types of inputs',
 'One row per student; Fall 2024–Spring 2026. Current analysis uses the saved processed table.',
 '''I have 191 distinct students from six course terms. I use assessment percentages, two logged LMS activity measures, three EVC-style survey features and wellness. The current table contains early expectancy, value and a cost field renamed cost_support. I have not revalidated its questionnaire scoring, so I do not interpret a positive cost score as automatically better or worse. All four early survey measures are missing for 78 students. The earlier notebook explicitly excluded a separate MLC RETRO export. That export and the raw ZIP are not present here, so I cannot claim that I tested retrospective responses. If those responses were collected after the forecast date, using them for an earlier prediction would leak later information.''')
for x,t,b,c in [(.7,'Grades','10-score or 16-score bundle\nRelease dates unverified',BLUE),(3.75,'LMS activity','Log page views\nLog participations',TEAL),(6.8,'EVC','Expectancy, value\nSource cost/support field',PURPLE),(9.85,'Wellness','Early self-report\nStudent mean',ORANGE)]:s.card(x,2.7,2.8,2.1,t,b,c)
s.rect(.7,5.15,11.95,1.08,'#FFF1DE',radius=True)
s.text(.92,5.36,11.5,.7,'78/191 lack early surveys. The separate MLC RETRO export was unavailable and was not analyzed.',18,ORANGE,True);s.finish()

s=Slide('03 / The role of the DAG','A useful map does not establish predictive value',
 'The original fixed DAG is preserved. Its arrows encode modeling assumptions.',
 '''I still think the DAG is useful as a transparent map of assumptions, but a plausible drawing does not show that every data source improves forecasting. In the original full graph, all six non-grade predictors and all sixteen grade variables are direct parents of the final outcome. With complete inputs, that final conditional distribution is a Bayesian regression, so I can test it directly without changing the other arrows. The predictor graph matters when missing inputs are inferred. In this new controlled comparison I instead fill missing values with training medians in every model. This gives a consistent comparison, but it is not full Bayesian inference over missing inputs, and it is not a test of the original graph's causal correctness. Conditioning on grades may also remove pathways through which motivation matters.''')
for i,(t,c) in enumerate([('EVC',PURPLE),('Wellness',ORANGE),('LMS',TEAL),('Grades',BLUE)]):
 y=2.55+i*.82;s.rect(.95,y,2.45,.62,c,radius=True);s.text(1.12,y+.12,2.1,.4,t,17,WHITE,True);s.line(3.5,y+.31,7.5,4.1,c)
s.rect(7.6,3.35,4.3,1.55,NAVY,radius=True);s.text(7.9,3.65,3.7,.9,'Final course percentage\n+ uncertainty',23,WHITE,True)
s.text(.95,6.2,11.5,.45,'Grouped outcome-parent view only; original predictor-to-predictor arrows are omitted here.',11,MUTED);s.finish()

s=Slide('04 / What posterior probability means','Three different questions need three different checks',
 'A likely positive coefficient is not the same as improved prediction.',
 '''I interpret your suggestion about posterior probabilities in three ways. The first is a coefficient probability, such as the probability that the page-view association is positive after conditioning on grades and the other inputs. The second is a student outcome probability, such as the chance of finishing below an illustrative 70 percent. Both come from the Bayesian outcome model. The third question is whether adding a data group reduces prediction error. I test that using paired later-term comparisons. I also use a Bayesian bootstrap to describe uncertainty about reweighting the four observed term gains. That bootstrap probability is separate from the coefficient posterior and is not the probability that the model will improve in a new course term.''')
s.card(.7,2.65,3.8,3.1,'1  Relationship','How plausible is a positive or practically large weight?\n\nConditional coefficient posterior.',PURPLE)
s.card(4.75,2.65,3.8,3.1,'2  Outcome','How likely is a student to finish below 70%?\n\nPosterior predictive probability.',TEAL)
s.card(8.8,2.65,3.8,3.1,'3  Added value','Do later students receive better predictions?\n\nPaired errors + term bootstrap.',BLUE)
s.text(.85,6.15,11.6,.4,'These are associations and forecasts; none establishes a coaching effect.',16,ORANGE,True);s.finish()

s=Slide('05 / Simulation and MCMC','The sampler agrees with the exact Bayesian solution',
 'The present linear Gaussian model has a closed-form posterior; MCMC is a validation exercise here.',
 '''I drew 20,000 independent samples from the exact conjugate posterior and also ran an actual two-block Gibbs sampler. Gibbs alternately updates the regression weights and residual variance. There are four chains, each with 1,000 warmup iterations followed by 4,000 saved iterations. The chains agree with the analytic posterior means and intervals. The largest rank-normalized R-hat is about 1.0007 and the smallest bulk effective sample size is above 12,000. Those checks support numerical accuracy for this model. They do not validate the assumed likelihood, graph, missing-data treatment or real-world forecasting performance. Since an exact solution exists, I would normally use it. MCMC becomes more useful if I add a robust likelihood, term effects or an explicit missing-data model.''')
s.image(OUT/'gibbs_trace.png',.7,2.5,8.15,3.8)
s.card(9.05,2.7,3.55,1.25,'4 chains','16,000 retained Gibbs draws',TEAL)
s.card(9.05,4.12,3.55,1.65,f'R-hat ≤ {checks["max_Rhat"]:.4f}',f'Minimum bulk ESS: {checks["min_bulk_ESS"]:,.0f}\nExact means within 2.01 MCSE',BLUE)
s.text(.85,6.45,11.7,.3,'Outcome conditional model only; this is not a sampler for the full missing-data DAG.',11,MUTED);s.finish()

s=Slide('06 / Fair prediction comparisons','Train on earlier terms; predict the next term',
 'Four checks, 146 later-student predictions per model. Every model uses the same evaluation students.',
 '''I evaluate Spring 2025, Fall 2025, Winter 2026 and Spring 2026 in order. Each time, training uses only terms before the evaluation term. Imputation values and scaling are fitted only on those training students. For each fold, I run the eight combinations of LMS, EVC and wellness in three contexts: no grades, the first grade bundle and the second grade bundle. That is 24 comparisons per fold, or 96 fits in the main analysis. I inherit coefficient precision 10 from the explored original workflow and check alternative priors rather than selecting a winner from these new results. The same records and settings have been examined before, and the training windows overlap, so I describe these as exploratory temporal checks, not independent confirmatory experiments. Grade-release dates remain unknown.''')
s.table(['Learn from','Check on','Students'],[
 ['Fall 2024 + Winter 2025','Spring 2025','43'],['Through Spring 2025','Fall 2025','20'],['Through Fall 2025','Winter 2026','40'],['Through Winter 2026','Spring 2026','43']], [5.5,4.8,1.65],y=2.5,rowh=.57)
s.text(.85,5.65,11.6,.65,'Three contexts: no grades / Block A (10 scores) / Block B (16 scores).',17,TEAL,True)
s.text(.85,6.38,11.6,.3,'Retrospective evidence bundles—not verified week-4 forecasts. All findings remain exploratory.',11,ORANGE);s.finish()

s=Slide('07 / Main result','Adding all three sources did not meaningfully reduce error',
 'Macro MAE: average of the four term errors, in final-percentage points. Lower is better.',
 '''The grade scores carry most of the predictive information in these comparisons. Without grades, the mean baseline has an average error of 6.54 points and all three extra sources give 6.52. That difference is only about 0.014 points. With the first grade bundle, error increases from 3.61 to 3.70. With the larger bundle, it increases from 2.95 to 3.04. The larger-bundle combined model is worse in all four term checks. This does not mean the extra sources are useless in every model or setting. It means this particular processed representation and model do not demonstrate meaningful incremental MAE benefit. These are new four-term macro results, not the original single Spring 2026 table of 2.82 versus 2.83.''')
rows=[]
for ct in ['No grades','Block A','Block B']:
 d=macro[macro.context.eq(ct)].set_index('group');a=d.loc['Baseline','MAE'];b=d.loc['LMS+EVC+Wellness','MAE'];rows.append([ct,f'{a:.2f}',f'{b:.2f}',f'{a-b:+.3f}'])
s.table(['Available grades','Baseline','+ LMS + EVC + wellness','MAE reduction'],rows,[3.1,2.1,4.35,2.4],y=2.75,rowh=.7,size=18)
s.text(.9,6.02,11.5,.55,'Block B: all-source MAE worsened in 4 of 4 later-term checks.',20,ORANGE,True);s.finish()

s=Slide('08 / Signal before grades','LMS shows a modest signal when grades are absent',
 'Exploratory source checks: no grade inputs; the same four later terms and students.',
 'I do not want the full-model comparison to hide a useful source-specific result. Without any grades, LMS activity alone reduces macro average error from 6.54 to 6.36 points, a gain of 0.177 points. All four evaluation terms improve. This is a modest signal, and it also appears under the two alternative shrinkage strengths, although its size changes. LMS plus wellness gives a similar 0.198-point gain, so this does not establish a separate wellness contribution. EVC alone worsens MAE in all four checks. Adding every source together reduces the improvement to only 0.014 points. The no-grades setting is a controlled evidence scenario, not a verified early-course forecast. These are multiple exploratory comparisons on already examined records, so I would use the LMS finding to guide a dated follow-up analysis rather than declare it a selected winning model.')
rows=[]
for group,pretty in [('LMS','LMS activity'),('Wellness','Wellness'),('EVC','EVC'),('LMS+Wellness','LMS + wellness'),('LMS+EVC+Wellness','All three sources')]:
 d=macro[macro.context.eq('No grades')].set_index('group');r=gains[gains.context.eq('No grades')&gains.extended.eq(group)&gains.comparison.eq('add_to_baseline')].iloc[0]
 rows.append([pretty,f'{d.loc[group,"MAE"]:.2f}',f'{r.macro_MAE_gain:+.3f}',f'{int(r.terms_improved)}/4'])
s.table(['Inputs beyond mean baseline','Macro MAE','MAE reduction','Terms better'],rows,[5.0,2.3,2.65,2.0],y=2.5,rowh=.57,size=15)
s.text(.85,6.25,11.6,.4,'Mean baseline MAE = 6.54. No-grades scenarios do not establish a verified prediction date.',12,ORANGE,True);s.finish()

s=Slide('09 / Which source helps?','No single addition shows a stable Block B MAE gain',
 'Positive means a reduction in error relative to the same grades-only baseline.',
 '''I also checked the sources individually and in pairs, rather than only comparing grades with the full model. Adding LMS alone, EVC alone or wellness alone gives a small negative average MAE gain in the larger grade context. Removing each group from the full model is also included in the output tables. The intervals shown here come from a Bayesian bootstrap over the four observed term mean gains. They describe sensitivity to how these four terms are weighted. They do not cover every possible future term or uncertainty in model development. In particular, when all four term gains are negative, every positive-weight bootstrap average is negative. A bootstrap probability of zero improvement then follows from the observed support; it is not proof that future improvement is impossible.''')
s.image(OUT/'paired_gains.png',.65,2.45,9.4,3.95)
s.card(10.15,2.8,2.5,2.8,'Interpretation','Changes are small. Do not treat four terms as strong evidence about every future class.',ORANGE)
s.text(.85,6.5,11.6,.25,'Intervals: 95% term Bayesian bootstrap; dotted line = illustrative 0.5-point useful gain.',10,MUTED);s.finish()

s=Slide('10 / What the weights say','Small conditional associations after grades are included',
 'Final fit: earlier 148 students. Effects are percentage points per one training standard deviation.',
 '''After fitting the larger grade model to the earlier 148 students, the page-view coefficient has an 89 percent posterior probability of being positive. However, its mean association is only 0.34 final-percentage points per training standard deviation. Its probability of exceeding one point in absolute value is below one percent. The other five non-grade coefficients also have less than one percent probability of an absolute effect above one point under this particular model. These statements are conditional on the prior, median-filled design, other predictors and fixed linear model. Grades may mediate or already summarize earlier engagement and motivation. Correlation among predictors and measurement error also affect coefficients. These are not posterior edge-existence probabilities, and they do not show that wellness or motivation has no broader educational or causal importance.''')
s.image(OUT/'coefficient_posteriors.png',.65,2.5,8.6,3.8)
s.card(9.45,2.85,3.15,2.65,'Page views', 'P(weight > 0): 88.9%\nMean: +0.34 points / SD\nP(|weight| > 1): 0.88%',PURPLE)
s.text(.85,6.4,11.6,.4,'All six non-grade P(|weight| > 1 point) values are below 1% in this conditional model.',12,MUTED);s.finish()

s=Slide('11 / Outcome probabilities','A probability is useful—and can still be wrong',
 'Illustrative question: P(final percentage < 70). This is not an official intervention threshold.',
 '''The model now reports an explicit probability distribution for each outcome. For one complete-input Spring 2026 student, the predicted mean is 71.24, the 90 percent interval is 65.72 to 76.75, and the probability of finishing below 70 is 35.6 percent. The actual final result was 75.95. For another student, whose surveys were missing and filled from training medians, the model assigned only a 2.3 percent probability below 70, but the actual outcome was 68.03. The 90 percent interval missed that result. A separate extreme outcome of 20.01 was predicted near 45.91, so the model also missed its severity. Integrating parameter uncertainty does not automatically fix those failures. These reused examples are diagnostics; they do not establish calibration or safe early-warning decisions.''')
s.card(.7,2.7,5.8,2.95,'Example with complete inputs','Predicted mean: 71.24%\n90% interval: 65.72–76.75%\nP(final < 70): 35.6%\nRecorded result: 75.95%',TEAL)
s.card(6.8,2.7,5.8,2.95,'A low outcome the model missed','Predicted mean: 77.60%\n90% interval: 71.36–83.83%\nP(final < 70): 2.3%\nRecorded result: 68.03%',ORANGE)
s.text(.85,6.12,11.7,.5,'The missed case had missing surveys. Imputed values are treated as fixed, so uncertainty is incomplete.',14,ORANGE,True);s.finish()

s=Slide('12 / Sensitivity checks','The diagnosis survives several reasonable alternatives',
 'Gain from adding all three sources to Block B; positive is better.',
 '''I reran the comparisons with weaker and stronger coefficient shrinkage, with missingness flags, and on students with complete non-grade inputs. The mean gain from adding all three sources to the larger grade bundle remains negative in every version. It is about minus 0.19 with precision 1, minus 0.088 with precision 10, minus 0.007 with precision 100, minus 0.119 with missingness indicators, and minus 0.106 for respondents. The respondent analysis changes the population and does not solve selection bias. The no-grades result is more prior-sensitive: its full-model gain ranges from about minus 0.099 to plus 0.082 over precisions 1 to 100. I would not interpret those small changes as a robust practical benefit. The detailed output also includes log scores, interval coverage, widths and Brier scores.''')
sens=pd.read_csv(OUT/'sensitivity_gains.csv');rows=[['Main: precision 10','−0.088']]
for name,pretty in [('precision_1','Weaker shrinkage: precision 1'),('precision_100','Stronger shrinkage: precision 100'),('missingness_indicators','Add missingness flags'),('respondents_only','Complete non-grade respondents')]:
 r=sens[(sens.sensitivity.eq(name))&(sens.context.eq('Block B'))&(sens.comparison.eq('add_to_baseline'))&(sens.extended.eq('LMS+EVC+Wellness'))].iloc[0];rows.append([pretty,f'{r.macro_MAE_gain:+.3f}'])
s.table(['Alternative','Block B MAE reduction'],rows,[8.4,3.55],y=2.45,rowh=.56,size=16)
s.text(.85,6.25,11.6,.45,'No-grades gains change with the prior; respondent-only results apply to a selected population.',12,ORANGE);s.finish()

s=Slide('13 / My diagnosis','Good exploratory framework; predictive claims need restraint',
 'I would keep the Bayesian baseline and improve the data and likelihood before making the model more complex.',
 '''My assessment is that this is a good capstone framework for transparent exploratory prediction and uncertainty. It is not evidence that the specified graph is causal or that a coaching system will improve grades. Assessment marks are components of the final percentage, so their predictive strength is partly a part-whole relationship and may reflect late-course information. Missing survey responses, unknown release dates and only six terms limit the current analysis. The Gaussian model also misses some low outcomes and ignores uncertainty in imputed inputs. I would not add MCMC just to make the method sound more Bayesian. The sampler is already validated against a tractable reference. I would first verify measurement and timing, then consider a robust likelihood, term-level partial pooling or explicit missing-data modeling if those choices improve the diagnosed weaknesses.''')
s.card(.7,2.65,3.8,3.35,'Keep','Transparent assumptions\nTemporal evaluation\nExact Bayesian baseline\nPosterior uncertainty',TEAL)
s.card(4.75,2.65,3.8,3.35,'Improve','Grade availability\nSurvey scoring / response\nLow-outcome fit\nMissing-data uncertainty',BLUE)
s.card(8.8,2.65,3.8,3.35,'Do not conclude','Arrows prove causality\nMCMC guarantees accuracy\nExtra surveys never help\nCoaching benefit shown',ORANGE);s.finish()

s=Slide('14 / Concrete next steps','Use the existing records to answer a sharper question',
 'A new class can strengthen confirmation later; it is not required to finish this exploratory capstone.',
 '''My next step is to recover the original data archive and verify when each grade and survey response became available. I would confirm the EVC and cost item wording and distinguish the early survey from the separate retrospective export. Then I would choose one useful forecast checkpoint and repeat the same paired source comparisons using only records available by that time. If retrospective responses occurred after that checkpoint, I would analyze them only as a separate retrospective association study. I would ask you to agree on a useful size of prediction gain and an appropriate risk threshold before interpreting probabilities as operational decisions. Finally, if low outcomes remain poorly represented, I would test a robust or hierarchical model against this fixed Bayesian baseline. An honest finding of no added predictive value is a valid research result.''')
items=[('1','Recover dates and measurement definitions','Grade release/revision snapshots; early EVC versus separate MLC RETRO.'),('2','Choose one useful forecast checkpoint','Use only inputs available then; retain the same students in comparisons.'),('3','Agree on what improvement would matter','The 0.5-point gain and 70% risk threshold used here are illustrative.'),('4','Address specific model failures','Test robust tails, term pooling or missing-data models against this baseline.')]
for i,(num,t,b) in enumerate(items):
 y=2.55+i*.91;s.rect(.75,y,.55,.55,TEAL,radius=True);s.text(.9,y+.1,.3,.35,num,17,WHITE,True);s.text(1.55,y,10.8,.4,t,17,NAVY,True);s.text(1.55,y+.42,10.8,.35,b,11.5,MUTED)
s.finish()

s=Slide('Appendix A / Reproducible mathematics','One posterior; two sampling routes',
 'Normal–Inverse-Gamma regression, conditional on training-only preprocessing and imputed inputs.',
 '''The standardized response z equals A beta plus Gaussian noise. The coefficient prior is normal conditional on residual variance, with precision 0.001 for the intercept and 10 for slopes. The variance prior is inverse-gamma with shape 2 and scale 1. The posterior has precision L, mean m, shape a and scale b. Direct simulation draws variance from its inverse-gamma marginal and beta from its conditional normal. Gibbs draws beta conditional on the current variance, then variance conditional on beta. The second conditional adds p over two to the inverse-gamma shape and a quadratic coefficient deviation to the scale. For a new fixed design row, integrating both parameter types gives an exact Student-t predictive distribution. This is why exact simulation is available and MCMC is optional for this model.''')
s.rect(.7,2.5,11.95,3.75,WHITE,BORDER,True)
s.text(.95,2.7,11.45,3.35,'z = Aβ + ε;    ε ~ Normal(0, σ²I)\nβ | σ² ~ Normal(0, σ²Λ₀⁻¹);    σ² ~ InvGamma(2, 1)\nL = Λ₀ + AᵀA;    m = L⁻¹Aᵀz;    a = 2 + n/2\nb = 1 + ½(zᵀz − mᵀLm)\nDirect: σ² ~ IG(a,b), then β | σ² ~ Normal(m, σ²L⁻¹)\nGibbs variance step: IG(a+p/2, b+½(β−m)ᵀL(β−m))\nNew outcome: Student-t with df = 2a, location A* m, scale² = (b/a)(1+A* L⁻¹A*ᵀ)',17,NAVY)
s.text(.85,6.45,11.5,.3,'Parameters above are in standardized units; predictions are transformed back to final-percentage points.',10,MUTED);s.finish()

s=Slide('Appendix B / Reading the scores','Evaluate distributions as well as point errors',
 'Four-term macro results for Block B. The 70% Brier threshold is illustrative.',
 '''I score predictive distributions with negative log predictive density, where lower is better, and also report interval coverage, interval width and a Brier score for the illustrative below-70 event. I use the unbounded Student-t density and unbounded intervals; clipping is applied only to point predictions for MAE. Coverage near 90 percent on a small reused sample does not prove calibration, especially for low outcomes. The full model has slightly worse log score and slightly wider intervals, while its Brier score is only marginally lower. That mixed pattern does not justify claiming a clear distributional improvement. The original all-student DAG marginalized missing prediction inputs using fixed joint parameters. The new comparison fills those inputs and integrates outcome parameter uncertainty, so the two all-student procedures should not be described as identical.''')
b=macro[macro.context.eq('Block B')].set_index('group')
rows=[]
for title,key in [('MAE ↓','MAE'),('Negative log density ↓','NLPD'),('90% interval coverage','coverage90'),('Mean interval width ↓','width90'),('Brier score below 70 ↓','Brier70')]:
 rows.append([title,f'{b.loc["Baseline",key]:.4f}',f'{b.loc["LMS+EVC+Wellness",key]:.4f}'])
s.table(['Metric','Grades only','All sources'],rows,[6.4,2.8,2.75],y=2.45,rowh=.56)
s.text(.85,6.25,11.5,.4,'Near-nominal coverage is not proof of calibrated low-outcome probabilities.',13,ORANGE,True);s.finish()

s=Slide('Appendix C / Scope and references','What was run, and what remains unverified',
 'All new tables, plots, code and executed notebook accompany this presentation.',
 '''The analysis used the existing processed table, whose hash and package versions are recorded in provenance.json. It fit all eight source combinations under three grade contexts across four later terms, repeated the experiment under four sensitivity settings, drew 20,000 exact posterior samples and ran four Gibbs chains. The executed notebook and tests document the run. The raw ZIP and separate MLC RETRO export remain unavailable, so extraction, survey reliability and retrospective-response timing are not newly verified. No posterior causal edge probabilities or deployed coaching claims are made. The methodological references identify standard Bayesian regression, Bayesian bootstrap and MCMC diagnostic methods; they are not sources of our empirical results.''')
s.text(.85,2.5,11.65,1.2,'Reproducible: MLC_Posterior_Predictive_Value.ipynb + posterior_study/\nEvidence: posterior_results/ + POSTERIOR_STUDY.md\nPreserved: original DAG notebook, original results, and supplied presentation.',16,NAVY)
s.text(.85,3.95,11.65,.9,'Unverified: raw-data extraction; separate RETRO effects; grade timing; causal effects; prospective calibration.',16,ORANGE,True)
s.text(.85,5.08,11.65,1.4,'Method references\nMurphy (2012), Machine Learning: A Probabilistic Perspective, Bayesian linear regression.\nRubin (1981), The Bayesian Bootstrap. DOI: 10.1214/aos/1176345338.\nVehtari et al. (2021), Rank-Normalization, Folding, and Localization. DOI: 10.1214/20-BA1221.',11,MUTED);s.finish()

prs.save(DEST/'MLC_posterior_updated.pptx');pdf.save()
(DEST/'MLC_posterior_speaker_notes.md').write_text('# First-person speaker notes\n\n'+'\n\n'.join(f'## {i}. {t}\n\n{note}' for i,(t,note) in enumerate(notes,1)))
print(f'Saved {len(prs.slides)} editable slides, PDF, and notes to {DEST}')

# A printable rehearsal copy of the exact embedded first-person notes.
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape
note_title=ParagraphStyle('note_title',fontName='DVB',fontSize=17,leading=23,spaceAfter=20)
note_body=ParagraphStyle('note_body',fontName='DV',fontSize=12,leading=19)
flow=[]
for i,(title,note) in enumerate(notes,1):
 if i>1:flow.append(PageBreak())
 flow.extend([Paragraph(escape(f'{i}. {title}'),note_title),Paragraph(escape(note),note_body)])
SimpleDocTemplate(str(DEST/'MLC_posterior_speaker_notes.pdf'),rightMargin=55,leftMargin=55,topMargin=65,bottomMargin=55).build(flow)
