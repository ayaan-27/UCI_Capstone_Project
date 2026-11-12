"""Package one current presentation/report plus all project evidence and archives.

python -m posterior_study.create_release --output /workspace/MLC_Capstone_Complete
Optional --reference files are archived as user-provided context, never executed.
This packages completed results; it does not rerun or claim new model fits.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
from xml.sax.saxutils import escape
import pandas as pd
from PIL import Image as PILImage, ImageDraw
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit,ImageReader
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image as PDFImage,Preformatted
from matplotlib import font_manager
from .analysis import ROOT

NAVY='#15273F';TEAL='#0F766E';BLUE='#2563EB';PURPLE='#8050AD';ORANGE='#B45309';MUTED='#56677C';BG='#F6F8FC';WHITE='#FFFFFF';BORDER='#DCE3ED'
W,H=13.333333,7.5

def register_fonts():
    pdfmetrics.registerFont(TTFont('MLC',font_manager.findfont('DejaVu Sans')))
    pdfmetrics.registerFont(TTFont('MLCB',font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans',weight='bold'))))
    pdfmetrics.registerFontFamily('MLC',normal='MLC',bold='MLCB',italic='MLC',boldItalic='MLCB')

def rgb(c):return tuple(int(c[i:i+2],16)/255 for i in (1,3,5))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mdtable(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])

def evidence():
    p=ROOT/'posterior_results';r=ROOT/'retro_followup_results';g=ROOT/'grading_results'
    e={name:pd.read_csv(path) for name,path in {
        'macro':p/'macro_metrics.csv','coeff':p/'coefficient_posteriors.csv','gains':p/'paired_gain_summary.csv',
        'terms':p/'paired_term_gains.csv','retro':r/'retro_paired_gains.csv','bench':r/'model_benchmark_macro.csv',
        'weights':g/'category_weights.csv','risk':p/'spring2026_probabilities.csv'}.items()}
    e['prov']=json.loads((p/'provenance.json').read_text());e['retro_prov']=json.loads((r/'retro_provenance.json').read_text());e['weight_prov']=json.loads((g/'weight_audit.json').read_text())
    e['overview']=[]
    for ct in ['No grades','Block A','Block B']:
        m=e['macro'][e['macro'].context.eq(ct)].set_index('group')
        a=float(m.loc['Baseline','MAE']);b=float(m.loc['LMS+EVC+Wellness','MAE'])
        e['overview'].append([ct,f'{a:.3f}',f'{b:.3f}',f'{a-b:+.3f}'])
    e['retro_b']=e['retro'].query("context == 'Block B' and base == 'Baseline' and alpha == 10 and scope == 'All students'")
    return e

class Deck:
    def __init__(self,dest):
        self.dest=dest;dest.mkdir(parents=True,exist_ok=True)
        self.prs=Presentation();self.prs.slide_width=Inches(W);self.prs.slide_height=Inches(H)
        self.pdf=canvas.Canvas(str(dest/'MLC_Consolidated_Presentation.pdf'),pagesize=(W*72,H*72))
        self.pdf.setTitle('My Learning Coach — consolidated research presentation')
        self.notes=[];self.autosizes=[]
    def slide(self,title,subtitle,note,appendix=False):return Slide(self,title,subtitle,note,appendix)
    def save(self):
        self.prs.save(self.dest/'MLC_Consolidated_Presentation.pptx');self.pdf.save()
        (self.dest/'Speaker_Notes.md').write_text('# Consolidated first-person speaker notes\n\n'+'\n\n'.join(f'## {i}. {t}\n\n{n}' for i,(t,n) in enumerate(self.notes,1)))
        sty=ParagraphStyle('notes',fontName='MLC',fontSize=11.5,leading=18)
        title=ParagraphStyle('ntitle',fontName='MLCB',fontSize=17,leading=23,spaceAfter=18)
        flow=[]
        for i,(t,n) in enumerate(self.notes,1):
            if i>1:flow.append(PageBreak())
            flow += [Paragraph(escape(f'{i}. {t}'),title),Paragraph(escape(n),sty)]
        SimpleDocTemplate(str(self.dest/'Speaker_Notes.pdf'),leftMargin=55,rightMargin=55,topMargin=60,bottomMargin=50).build(flow)
        (self.dest/'layout_audit.json').write_text(json.dumps({'slide_count':len(self.notes),'minimum_text_pt':min(self.autosizes),'native_text_and_shapes':True,'figures':'embedded PNGs; full-resolution sources in project result folders','pdf':'rendered from common layout with identical wrapping; not office-converted'},indent=2))

class Slide:
    def __init__(self,deck,title,subtitle,note,appendix):
        self.d=deck;self.s=deck.prs.slides.add_slide(deck.prs.slide_layouts[6]);self.title=title;self.note=note
        self.s.background.fill.solid();self.s.background.fill.fore_color.rgb=RGBColor.from_string(BG[1:])
        deck.pdf.setFillColorRGB(*rgb(BG));deck.pdf.rect(0,0,W*72,H*72,stroke=0,fill=1)
        self.rect(.5,.47,.12,.3,TEAL)
        self.text(.8,.46,11,.35,('APPENDIX' if appendix else 'MY LEARNING COACH')+f'  /  {len(deck.prs.slides):02}',11,TEAL,True)
        self.text(.65,1.02,12.05,.72,title,27,NAVY,True)
        self.text(.67,1.78,12,.57,subtitle,12,MUTED)
    def rect(self,x,y,w,h,c=WHITE,radius=True):
        shape=self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
        shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(c[1:]);shape.line.fill.background()
        pdf=self.d.pdf;pdf.setFillColorRGB(*rgb(c))
        if radius:pdf.roundRect(x*72,(H-y-h)*72,w*72,h*72,8,stroke=0,fill=1)
        else:pdf.rect(x*72,(H-y-h)*72,w*72,h*72,stroke=0,fill=1)
    def text(self,x,y,w,h,txt,size=16,c=NAVY,bold=False):
        font='MLCB' if bold else 'MLC'
        while True:
            lines=[]
            for p in str(txt).split('\n'):lines.extend(simpleSplit(p,font,size,w*72-3) if p else [''])
            leading=size*1.25
            if len(lines)*leading<=h*72+1:break
            size-=.5
            if size<9:raise ValueError(f'Text box too dense: {self.title}: {txt}')
        self.d.autosizes.append(size)
        tf=self.s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame
        tf.clear();tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=False
        for i,line in enumerate(lines):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(c[1:]);p.space_after=Pt(0);p.space_before=Pt(0);p.line_spacing=Pt(leading)
            pdf=self.d.pdf;pdf.setFont(font,size);pdf.setFillColorRGB(*rgb(c));pdf.drawString(x*72,(H-y)*72-size-i*leading,line)
    def line(self,x1,y1,x2,y2,c=MUTED):
        line=self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2));line.line.color.rgb=RGBColor.from_string(c[1:]);line.line.width=Pt(1.5)
        pdf=self.d.pdf;pdf.setStrokeColorRGB(*rgb(c));pdf.setLineWidth(1.5);pdf.line(x1*72,(H-y1)*72,x2*72,(H-y2)*72)
    def image(self,path,x,y,w,h):
        iw,ih=PILImage.open(path).size;scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale;x+=(w-dw)/2;y+=(h-dh)/2
        self.s.shapes.add_picture(str(path),Inches(x),Inches(y),Inches(dw),Inches(dh));self.d.pdf.drawImage(ImageReader(str(path)),x*72,(H-y-dh)*72,dw*72,dh*72)
    def card(self,x,y,w,h,title,body,c=TEAL):
        self.rect(x,y,w,h);self.text(x+.2,y+.2,w-.4,.55,title,19,c,True);self.text(x+.2,y+.85,w-.4,h-1.02,body,15)
    def table(self,headers,rows,widths,y=2.55,rowh=.57,size=14):
        for j,row in enumerate([headers]+rows):
            x=.7
            for v,w in zip(row,widths):
                self.rect(x,y+j*rowh,w,rowh-.02,NAVY if j==0 else WHITE,False)
                self.text(x+.12,y+j*rowh+.1,w-.24,rowh-.14,v,12 if j==0 else size,WHITE if j==0 else NAVY,j==0);x+=w
    def finish(self):
        self.line(.65,7.0,12.7,7.0,BORDER);self.text(.68,7.12,10.8,.23,'UCI CAPSTONE  /  CONSOLIDATED FINDINGS  /  EXPLORATORY NON-SUMMER STUDY',9,MUTED)
        self.text(12.1,7.08,.5,.28,str(len(self.d.prs.slides)),10,TEAL,True)
        self.s.notes_slide.notes_text_frame.text=self.note;self.d.notes.append((self.title,self.note));self.d.pdf.showPage()


def presentation(dest,e,public=False):
    d=Deck(dest);p=ROOT/'posterior_results';r=ROOT/'retro_followup_results'
    s=d.slide('Which data improve final-grade predictions?', 'Bayesian DAG, posterior simulation, RETRO text, model comparisons, grading weights and summer exclusion.',
    'Professor, this presentation brings the work into one story. I start with the original Bayesian DAG and ask whether wellness, motivation, LMS activity and reflections improve predictions beyond grades. I implemented posterior simulation and a Gibbs MCMC check, compared sources on later students, analyzed the newly supplied RETRO text, benchmarked other models and audited the grading weights. My central finding is that the extra numeric sources do not improve average error beyond the larger grade bundle. LMS alone has a modest signal when grades are absent. These are exploratory findings from existing non-summer terms, and none establishes a causal effect.')
    s.card(.7,2.7,7.6,2.8,'Research question','What do the inputs add to predictions—and how uncertain are those conclusions?')
    s.rect(8.6,2.7,4.0,2.8,NAVY);s.text(8.85,3.0,3.5,.5,'Current conclusion',18,'#71E0CA',True);s.text(8.85,3.85,3.5,1.2,'Keep the simple grade-based baseline.',25,WHITE,True)
    s.text(.85,6.1,11.6,.5,'One current account of completed work; later improvements are labelled as proposals.',16,TEAL,True);s.finish()
    s=d.slide('191 students, six non-summer terms', 'Fall 2024–Spring 2026; one analysis row per student. SMR/Summer courses are excluded.',
    'The main analysis includes 191 distinct students from six Fall, Winter and Spring terms. The original early feature table has grades, logged LMS counts, EVC-style responses and wellness. Seventy-eight students lack the early survey measures. The new RETRO file adds a distinct text source for only the last three terms: 74 students have reflections at some point, and 68 have nonblank reflections in Week 2 or 4. I do not treat students in the earlier terms as nonrespondents to an instrument that was not available. Summer exclusion is explicit, and no existing student is removed because the current cohort was already non-summer.')
    for x,t,b,col in [(.7,'Grades','Block A: 10 scores\nBlock B: 16 scores',BLUE),(3.75,'LMS','Log page views\nLog participations',TEAL),(6.8,'EVC + wellness','Three EVC-style inputs\nOne wellness mean',PURPLE),(9.85,'RETRO text','Three open prompts\nThree covered terms',ORANGE)]:s.card(x,2.65,2.8,2.4,t,b,col)
    s.rect(.7,5.45,11.95,.95,'#FFF1DE');s.text(.92,5.65,11.5,.6,'78/191 lack early surveys. Exact grade-release and RETRO submission times remain unverified.',17,ORANGE,True);s.finish()
    s=d.slide('The DAG makes assumptions visible', 'The original fixed graph has 23 nodes and 62 arrows; its structure was not learned from correlations.',
    'The original fitted graph has six non-grade inputs, sixteen grade inputs and final percentage. Its arrows are assumed conditional relationships. Every input is a direct parent of the outcome. The grouped picture here shows those outcome parents; it omits the predictor-to-predictor arrows for readability. With all inputs observed, the outcome conditional distribution is Bayesian regression. The predictor graph matters when evidence is missing. A plausible map does not prove predictive value or causality, so I test sources separately. The complete original graph is included as SVG, PNG and DOT in the package.')
    for i,(t,c) in enumerate([('EVC',PURPLE),('Wellness',ORANGE),('LMS',TEAL),('Grades',BLUE)]):
        y=2.5+i*.84;s.rect(.95,y,2.5,.62,c);s.text(1.13,y+.1,2.14,.42,t,17,WHITE,True);s.line(3.55,y+.31,7.5,4.1,c)
    s.rect(7.6,3.3,4.3,1.6,NAVY);s.text(7.9,3.65,3.7,.9,'Final percentage\n+ uncertainty',23,WHITE,True)
    s.text(.95,6.25,11.4,.4,'Outcome-parent view only. Arrows are assumptions; causal and coaching effects are not established.',12,ORANGE);s.finish()
    s=d.slide('Three questions need different evidence', 'Posterior signs, individual outcome risk and predictive improvement are separate quantities.',
    'I separated three meanings of impact. First, a coefficient posterior describes plausible conditional associations after fitting the model. Second, a posterior predictive probability describes a student outcome under that model. Third, a paired later-term comparison measures whether an added source improves forecasts. The term Bayesian bootstrap used for error gains is not the same distribution as the coefficient posterior, and does not give a guaranteed chance of success in a new term. A continuous shrinkage coefficient also does not supply a probability that a causal edge exists.')
    for x,t,b,c in [(.7,'Association','How plausible is a positive or practically large conditional weight?',PURPLE),(4.75,'Outcome','What probability does the model assign to a final result below 70%?',TEAL),(8.8,'Added value','Does the source reduce error for the same later students?',BLUE)]:s.card(x,2.7,3.8,2.85,t,b,c)
    s.text(.9,6.05,11.5,.6,'Changing an input in a prediction is not evidence that intervening on it changes a grade.',17,ORANGE,True);s.finish()
    s=d.slide('Posterior simulation agrees with the exact solution', '20,000 independent posterior draws; four actual Gibbs MCMC chains.',
    'The current Normal–Inverse-Gamma model is conjugate, so an exact solution exists. I simulated 20,000 independent posterior draws and ran four actual Gibbs chains, each with 1,000 warmup and 4,000 retained iterations. Gibbs alternates coefficient and variance draws. The rank-normalized diagnostics and Monte Carlo errors agree with the analytic posterior. This supports computation, not the graph, likelihood or missing-data assumptions. MCMC is optional for this model; it would become more useful with a nonconjugate hierarchical or explicit missing-data model.')
    s.image(p/'gibbs_trace.png',.7,2.5,8.4,3.9)
    chk=e['prov']['simulation_checks'];s.card(9.3,2.8,3.3,2.65,'Numerical checks',f'Max R-hat: {chk["max_Rhat"]:.4f}\nMin bulk ESS: {chk["min_bulk_ESS"]:,.0f}\nMeans within 2.01 MCSE',TEAL)
    s.text(.85,6.5,11.5,.28,'Outcome-CPD sampling conditional on the imputed design—not full missing-data DAG inference.',11,MUTED);s.finish()
    s=d.slide('Learn from earlier terms; check later students', 'Four expanding-window evaluations; 146 later-student predictions per numeric model.',
    'For each check I fit imputation, scaling and the model using earlier terms only. I compare all eight combinations of LMS, EVC and wellness in three grade contexts. Every comparison uses the same evaluation students. Main precision 10 is inherited from the explored original workflow; sensitivity runs use 1 and 100, missingness flags and non-grade complete respondents. The training windows overlap and these records and settings have already been explored, so the results are exploratory rather than independent confirmation. The grade bundles are not verified week-four snapshots.')
    s.table(['Train through','Evaluate','Students'],[['Winter 2025','Spring 2025','43'],['Spring 2025','Fall 2025','20'],['Fall 2025','Winter 2026','40'],['Winter 2026','Spring 2026','43']],[5.3,4.9,1.75],y=2.5)
    s.text(.85,5.72,11.6,.65,'Compare: no grades / Block A / Block B. Main comparisons and all sensitivities are retained.',17,TEAL,True);s.text(.85,6.5,11.6,.28,'Historically explored data and settings; course timing is not verified.',11,ORANGE);s.finish()
    s=d.slide('All-source additions did not improve grade-based MAE', 'Macro MAE gives each evaluation term equal weight. Positive reduction means lower error.',
    'With no grades, all numeric sources give only a 0.014-point average improvement. With Block A, error rises from 3.61 to 3.70. With Block B, it rises from 2.95 to 3.04 and is worse in all four checks. These comparisons integrate outcome-parameter uncertainty but use median filling for missing prediction inputs. They differ from the original joint-Gaussian missing-evidence procedure. The old single Spring 2026 result of approximately 2.82 versus 2.83 is preserved, but is not the four-term macro result shown here.')
    s.table(['Grade evidence','Baseline','All numeric sources','MAE reduction'],e['overview'],[3.0,2.2,4.35,2.4],y=2.75,rowh=.7,size=18)
    s.text(.9,6.05,11.5,.55,'Block B combined model worsened MAE in all four later terms.',20,ORANGE,True);s.finish()
    s=d.slide('LMS has a modest signal when grades are absent', 'Exploratory source-specific comparison; a no-grades scenario is not itself a verified early forecast.',
    'The full-model comparison hides a useful nuance. Without grades, LMS alone reduces macro MAE from 6.54 to 6.36, an improvement of 0.177 points in all four terms. LMS plus wellness gives a similar 0.198-point gain, which does not establish a separate wellness benefit. EVC alone worsens MAE in all four terms. Adding every numeric source largely erases the LMS gain. The modest LMS association survives several shrinkage choices on average, but should guide a dated follow-up rather than be treated as a confirmed selected winner.')
    rows=[];ng=e['macro'][e['macro'].context.eq('No grades')].set_index('group')
    for g,name in [('LMS','LMS activity'),('Wellness','Wellness'),('EVC','EVC'),('LMS+Wellness','LMS + wellness'),('LMS+EVC+Wellness','All numeric sources')]:
        a=e['gains'].query("context == 'No grades' and comparison == 'add_to_baseline'").set_index('extended').loc[g];rows.append([name,f'{ng.loc[g,"MAE"]:.2f}',f'{a.macro_MAE_gain:+.3f}',f'{int(a.terms_improved)}/4'])
    s.table(['Inputs beyond mean baseline','MAE','MAE reduction','Terms better'],rows,[5.0,2.2,2.75,2.0],y=2.5)
    s.text(.85,6.35,11.5,.35,'The baseline is the earlier-student mean; its macro MAE is 6.54 points.',12,MUTED);s.finish()
    s=d.slide('Conditional effects are small and uncertain', 'Final fit: 148 earlier students. Final-percentage points per one training standard deviation.',
    'These coefficients hold grades and the other predictors fixed. Wellness has a mean conditional association of about plus 0.20 percentage points per training standard deviation, with an interval from minus 0.39 to plus 0.78. Every displayed interval includes zero. None is a causal effect per questionnaire point. Conditioning on grades may block pathways through which earlier motivation relates to outcomes, and the estimates depend on the prior and imputation. The cost/support label is the source cost field renamed by the old pipeline, not a newly validated or reverse-scored scale.')
    names={'log_page_views':'LMS page views','log_lms_participations':'LMS participations','cost_support':'EVC source cost/support','expectancy':'EVC expectancy','value':'EVC value','wellness':'Wellness'}
    s.table(['Input','Mean points / SD','95% credible interval'],[[names[a.feature],f'{a.mean_points_per_SD:+.2f}',f'[{a.lower95:+.2f}, {a.upper95:+.2f}]'] for a in e['coeff'].head(6).itertuples()],[5.3,2.9,3.75],y=2.45,rowh=.55)
    s.text(.85,6.52,11.5,.3,'All six P(|conditional weight| > 1 point) values are below 1%, conditional on this model.',11,ORANGE);s.finish()
    s=d.slide('The new RETRO source contains open reflections', '870 response rows; 74 students; Weeks 2, 4, 6, 8 and 10; all IDs match the existing records.',
    'The uploaded RETRO is a distinct instrument from numerical EVC. It asks what went well, what did not go well and what could improve motivation and engagement. I analyze nonblank Week 2 and Week 4 responses only in the initial scenario, giving 68 respondents. Weeks 6, 8 and 10 are excluded. Exact submission times are absent. Only the last three terms have this instrument, so only two later-term checks are possible. The first text model trains on 20 students, of whom just 13 supplied early text. This small sample limits how much a text model can learn.')
    s.table(['RETRO term','Grade-table students','Week 2/4 respondents'],[['Fall 2025','20','13'],['Winter 2026','40','25'],['Spring 2026','43','30']],[4,4,3.95],y=2.7)
    s.rect(.75,5.35,11.85,.95,'#FFF1DE');s.text(.95,5.55,11.4,.6,'Only week labels are available. Earlier terms are not coded as nonrespondents.',17,ORANGE,True);s.finish()
    s=d.slide('RETRO words show mixed added value', 'Train-only TF-IDF plus response measures; larger grades-only baseline; Ridge alpha 10.',
    'I separate the words from response behavior. Response measures include participation, number of answers and weeks, and word count. Then I add separate train-only TF-IDF channels for the three prompts. In the larger-grade scenario, words plus response measures reduce error by about 0.31 points in Winter but worsen it by about 0.04 in Spring. Response measures alone perform better on average, so I cannot attribute a reliable improvement to the words. These two-term comparisons use different training windows from the earlier four-term study. Alpha sensitivities and respondent-only comparisons are retained. This sparse text baseline is not validated factor scoring and does not show that the reflections contain no useful information.')
    s.image(r/'retro_gains.png',.65,2.45,9.0,3.95);s.card(9.9,2.85,2.7,2.85,'Interpretation','No consistent independent content benefit established.',PURPLE)
    s.text(.85,6.55,11.6,.25,'Two explored evaluation terms; no claim of an identified causal RETRO effect.',11,MUTED);s.finish()
    s=d.slide('Tested alternatives did not beat the grades baseline', 'Same four numeric temporal checks; fixed, modest candidate settings; point error only.',
    'I compared the Bayesian outcome model with Ridge, Huber robust regression, ExtraTrees and histogram gradient boosting. With the larger grades-only bundle, Bayesian and Ridge MAE is 2.95, Huber is 3.45, ExtraTrees is 4.27 and boosting is 4.32. Ridge and the Bayesian CPD have the same point forecast at the same penalty, so they are not independent discoveries. Some alternatives slightly help the no-grades full model, but the earlier Bayesian LMS-only MAE is still lower. This is not exhaustive tuning or a claim of the best possible model, and it does not compare posterior calibration of the alternatives.')
    s.image(r/'model_comparison.png',.65,2.4,9.25,4.0);s.card(10.0,2.95,2.55,2.75,'Decision','Keep the simple baseline while improving timing and measurement.',TEAL);s.finish()
    s=d.slide('Posterior probabilities can still miss low outcomes', 'Illustrative below-70 threshold; it is not an official pass/fail or intervention rule.',
    'For a complete-input Spring case, the model predicts 71.24 with a 35.6 percent probability below 70; the actual result is 75.95. Another case has a predicted mean of 77.60 and just a 2.3 percent below-70 probability, yet the actual result is 68.03. That student has missing surveys, filled from training medians. The model also predicts the extreme 20.01 outcome near 45.91 and misses severity. Parameter uncertainty alone does not fix these failures. Training posterior predictive checks do not establish later-term calibration, particularly with few low outcomes.')
    s.card(.7,2.7,5.8,2.95,'Complete-input example','Mean: 71.24%\n90% interval: 65.72–76.75%\nP(final < 70): 35.6%\nActual: 75.95%',TEAL)
    s.card(6.8,2.7,5.8,2.95,'A low result the model missed','Mean: 77.60%\n90% interval: 71.36–83.83%\nP(final < 70): 2.3%\nActual: 68.03%',ORANGE)
    s.text(.85,6.2,11.6,.5,'Missing-input uncertainty and unusual failures remain important model weaknesses.',15,ORANGE,True);s.finish()
    s=d.slide('Confirmed weights and explicit summer exclusion', 'The user confirmed the same main category weights for all six historical non-summer terms.',
    'The main weights sum to 100 percent: written categories 20 and 35, verbal categories 10 and 10, teamwork 10, growth mindset 10, and resilience and agency 5. Surveys can add 0.75 points and team-manager credit 0.25; the MLC extra-credit group is zero-weight here. I keep extra credit separate, rather than renormalizing to 101 percent. These are grading rules, not wellness or coaching effects. Summer courses are explicitly excluded; the current 191 students were already non-summer. The old manifest contains 168 SMR-labelled aggregate entries but none was used as a predictor.')
    main=e['weights'][~e['weights'].is_extra_credit]
    s.table(['Main grading category','Course weight'],[[a.category,f'{100*a.weight:g}%'] for a in main.itertuples()],[9,2.95],y=2.45,rowh=.47)
    s.text(.85,6.4,11.5,.55,'Extra credit: Surveys +0.75 points; Team Manager +0.25 points; MLC 0 points.',13,TEAL,True);s.finish()
    s=d.slide('Predict remaining performance after earned marks', 'Accounting is implemented and tested; real historical remaining-work targets are not yet reconstructed.',
    'A cleaner forecasting target separates already earned grade points from performance on remaining coursework. The final total equals the known contribution plus remaining course weight times normalized remaining performance, plus extra credit. The functions implement this accounting and use actual score-availability cutoffs. However, the aggregate feature table does not identify the full historical item catalog, denominators, unaggregated scores or extra credit. The workbook dates and roster are from course 84595 and cannot be backdated. Published and unpublished alternative versions also coexist. No historical remaining-work accuracy has been invented from those incomplete inputs.')
    s.rect(.75,2.6,11.85,1.5);s.text(1.0,2.85,11.35,1.0,'Final total = known earned contribution\n+ (1 − known course weight) × remaining main-work percentage\n+ extra credit',19,TEAL,True)
    s.text(.9,4.55,11.6,.65,'Category weights are confirmed. Effective historical assignments and availability still need verification.',17,NAVY,True)
    s.text(.9,5.65,11.6,.7,'Required next input: original complete grade exports/source ZIP, extra credit, and release/revision history.',16,ORANGE,True);s.finish()
    s=d.slide('Improve timing and measurement before complexity', 'A proposed longitudinal design—not a newly fitted or causally identified graph.',
    'My recommendation is to retain the simple baseline and improve the data-generating question. A mark can change later motivation and reflections; those measurements may help predict later engagement and marks. I would unroll those feedback paths over time, validate EVC scoring and human-coded RETRO themes, and include observed prior preparation and term context where available. A regularized hierarchical Bayesian model with robust residuals is worth testing after longitudinal inputs are recovered, but has not been fitted here and is not guaranteed to help. The existing six terms suffice for an exploratory capstone; new-class confirmation would strengthen it later.')
    for x,t,b,c in [(.8,'Earlier marks','Observed at time t',TEAL),(4.95,'Later EVC / RETRO','Measurements at time t+1',PURPLE),(9.1,'Future coursework','Activity / marks at t+2',NAVY)]:s.card(x,2.7,3.4,1.9,t,b,c)
    s.text(4.3,3.4,.5,.5,'→',24,MUTED,True);s.text(8.45,3.4,.5,.5,'→',24,MUTED,True)
    s.text(.95,5.15,11.5,1.35,'1  Verify a useful prediction date and remaining-work target.\n2  Validate survey scoring, RETRO themes and response patterns.\n3  Test restrained term pooling, robust residuals and missing-data models.',17,NAVY);s.finish()
    s=d.slide('Technical reference: exact Bayesian regression', 'Normal–Inverse-Gamma outcome CPD, conditional on training-only scaling and a fixed imputed design.',
    'In standardized units the coefficient prior is normal conditional on residual variance, with precision 0.001 for the intercept and 10 for slopes. Variance has inverse-gamma shape 2 and scale 1. The posterior parameters are L, m, a and b. Independent sampling draws variance from its inverse-gamma marginal and coefficients from their conditional normal. Gibbs instead alternates conditional coefficient and variance draws, adding p over two to the inverse-gamma shape in the variance step. Integrating coefficients and variance for a fixed new design gives an exact Student-t predictive distribution. This does not integrate uncertainty in imputation, model selection or the DAG structure.',True)
    s.rect(.7,2.5,11.95,3.75);s.text(.95,2.72,11.45,3.25,'z = Aβ + ε;  ε ~ Normal(0, σ²I)\nβ | σ² ~ Normal(0, σ²Λ₀⁻¹);  σ² ~ InvGamma(2,1)\nL = Λ₀ + AᵀA;  m = L⁻¹Aᵀz;  a = 2+n/2\nb = 1 + ½(zᵀz − mᵀLm)\nDirect: σ² ~ IG(a,b);  β | σ² ~ Normal(m, σ²L⁻¹)\nGibbs variance: IG(a+p/2, b+½(β−m)ᵀL(β−m))\nPredictive: Student-t, df=2a, location A*m, scale²=(b/a)(1+A*L⁻¹A*ᵀ)',17)
    s.text(.85,6.48,11.5,.3,'Predictive Student-t from a Gaussian likelihood is distinct from a robust Student-t likelihood.',11,ORANGE);s.finish()
    s=d.slide('Technical reference: sensitivity and score limits', 'All-source additions to Block B remain negative under the recorded sensitivity checks.',
    'The larger-grade full-model MAE gain is negative under precision 1, precision 10, precision 100, missingness indicators and complete non-grade respondents. Respondent-only analysis selects a different population and does not solve nonrandom response. The paired-gain Bayesian bootstrap reweights four observed term mean differences with Dirichlet weights. Its intervals do not include all development or future-term uncertainty. When all four gains are negative, every positive-weight average is negative, so a zero reported bootstrap improvement probability is not proof of universal impossibility. The 0.5-point practical gain and below-70 risk threshold are illustrative, not agreed operational requirements.',True)
    sens=pd.read_csv(p/'sensitivity_gains.csv');rows=[['Main: precision 10','−0.088']]
    for name,pretty in [('precision_1','Precision 1'),('precision_100','Precision 100'),('missingness_indicators','Missingness indicators'),('respondents_only','Complete non-grade respondents')]:
        a=sens.query("context == 'Block B' and comparison == 'add_to_baseline' and extended == 'LMS+EVC+Wellness'");v=a[a.sensitivity.eq(name)].iloc[0].macro_MAE_gain;rows.append([pretty,f'{v:+.3f}'])
    s.table(['Sensitivity','Macro MAE reduction'],rows,[8.4,3.55],y=2.5)
    s.text(.85,6.3,11.5,.4,'Term bootstrap ≠ coefficient posterior ≠ a calibrated probability of success in a new term.',13,ORANGE,True);s.finish()
    input_note=('Uploaded source files are omitted from the public GitHub package; local copies are required to recompute RETRO and workbook audits.' if public else 'The uploaded RETRO and weights inputs are included under the project data folder.')
    s=d.slide('Technical reference: evidence and reproducibility', 'The organized package contains current deliverables, results, code and input requirements.',
    'The package preserves the original notebook and full graph alongside the three executed companion notebooks. The study runs from the included processed table. '+input_note+' The original historical source ZIP remains unavailable, so the original raw workflow is not newly reproduced. Fourteen existing tests are rerun from the packaged project. Input hashes, package versions, MCMC checks, cohort exclusions and all per-term and per-student results are included. The study supports exploratory conditional prediction, not causal or prospective coaching claims. Standard references support the inference and diagnostics methods rather than our empirical results.',True)
    s.text(.85,2.55,11.6,1.35,'01_Presentation/  Consolidated deck, PDF, speaker notes\n02_Report/  Current research report and artifact index\n03_Project/  Four notebooks, code, tests and all result folders\n04_Diagrams/  Full original DAG + labelled temporal proposal\n05_Archive/  Earlier decks, reports and supplied reference material',16)
    s.text(.85,4.3,11.6,1.05,'14 tests pass. Remaining-work arithmetic is tested; a historical remaining-work model is not fitted. Historical release/revision snapshots remain missing.',17,ORANGE,True)
    s.text(.85,5.6,11.6,1.1,'Method references: Murphy (2012), Bayesian linear regression.\nRubin (1981), Bayesian Bootstrap, DOI 10.1214/aos/1176345338.\nVehtari et al. (2021), MCMC diagnostics, DOI 10.1214/20-BA1221.',11,MUTED);s.finish()
    d.save();return len(d.notes)

def report_sections(e):
    coeff=e['coeff'].head(6)
    names={'log_page_views':'LMS page views','log_lms_participations':'LMS participations','cost_support':'Source cost/support','expectancy':'Expectancy','value':'Value','wellness':'Wellness'}
    co_rows=[[names[a.feature],f'{a.mean_points_per_SD:+.3f}',f'[{a.lower95:+.3f}, {a.upper95:+.3f}]',f'{100*a.P_positive:.1f}%'] for a in coeff.itertuples()]
    rt=e['retro_b'];rr=[[a.term,str(a.n),f'{a.baseline_MAE:.3f}',f'{a.response_MAE_gain:+.3f}',f'{a.text_total_MAE_gain:+.3f}',f'{a.text_over_response_gain:+.3f}'] for a in rt.itertuples()]
    b=e['bench'];bb=b[b.context.eq('Block B')].pivot(index='model',columns='group',values='MAE')
    br=[[name,f'{bb.loc[name,"Baseline"]:.3f}',f'{bb.loc[name,"All sources"]:.3f}'] for name in ['Bayesian CPD','Ridge','Huber','ExtraTrees','HistGB']]
    w=e['weights'];wr=[[a.category,f'{100*a.weight:g}%'] for a in w[~w.is_extra_credit].itertuples()]
    chk=e['prov']['simulation_checks']
    return [
    ('Executive findings',[
        ('p','This is the current integrated account of the My Learning Coach capstone. It consolidates the original fixed Bayesian DAG, posterior simulation and Gibbs MCMC validation, temporal source ablations, newly supplied RETRO text, candidate-model benchmarks, confirmed grading weights and explicit summer exclusion. Earlier presentations and stage reports are archived, not treated as current guidance.'),
        ('p','The main conclusion is conditional and exploratory: adding all numeric non-grade sources did not improve MAE beyond the larger assessment bundle. LMS activity alone showed a modest signal without grades. RETRO words had mixed two-term gains; participation and verbosity explain at least part of the apparent benefit. None of these analyses establishes causal or coaching effects.'),
        ('table',(['Grade context','Baseline MAE','All numeric MAE','MAE reduction'],e['overview'])),
        ('bullets',['191 unique students, six Fall/Winter/Spring terms; Summer/SMR excluded.','20,000 exact posterior draws and four Gibbs chains agree with the analytic outcome model.','The supplied RETRO and weight files are now included in the runnable package.','Fourteen tests pass from the packaged project.','Weighted remaining-work arithmetic is implemented and tested; a real historical remaining-work forecasting model is not yet fitted.']),
        ('p','Use the consolidated presentation for the talk, this report for interpretation and scope, and 03_Project for runnable code and full evidence. The missing prerequisite is the original complete historical grade/source archive and verified score-availability history, not another round of MCMC.')]),
    ('Data, graph and scope',[
        ('table',(['Source','Available representation','Important limit'],[
            ['Grades','Block A: 10 scores; Block B: 16','Aggregated from final exports; releases unverified'],
            ['LMS','log(1+page views), log(1+participations)','Original assumed first-four-week window'],
            ['Early EVC / wellness','Expectancy, value, source cost/support, wellness','78/191 lack all four early survey features'],
            ['RETRO','Three open reflection prompts; Weeks 2/4 used','Three terms only; no exact submission timestamps'],
            ['Weights','Seven main categories + three extra-credit categories','Same weights confirmed; item versions differ by term']])),
        ('p','The main processed sample is 18 Fall 2024, 27 Winter 2025, 43 Spring 2025, 20 Fall 2025, 40 Winter 2026 and 43 Spring 2026 students. All 191 IDs are distinct, so these are student-course rows rather than repeated independent survey observations. The current table contains no summer students. The historical eligibility manifest contains 168 SMR-labelled category aggregate entries; zero entered either predictor bundle.'),
        ('p','The original fixed DAG contains 23 nodes and 62 arrows: six non-grade inputs, sixteen assessment nodes and final percentage. There are eight predictor-subgraph arrows, 32 arrows from expectancy/page views to the sixteen assessment nodes, and all 22 inputs are outcome parents. The structure is assumed, not learned as a causal discovery result. The full original SVG/PNG/DOT is in 04_Diagrams and the original results folder.'),
        ('p','With complete outcome-parent evidence, the outcome CPD is regularized Bayesian regression. The other predictor arrows matter for missing-evidence inference. The updated same-student comparison instead uses training-median filling at both training and prediction time, with train-only scaling. It integrates outcome parameter uncertainty conditional on that fixed imputed design, not uncertainty in missing values, preprocessing, structure, model selection or causality.'),
        ('p','The source cost variable was renamed cost_support in the original pipeline. Its item wording, direction and scale reliability have not been newly validated. RETRO is a separate free-text instrument and must not be described as the numerical EVC score. Some grades are components of the final target, creating part-whole predictive association. Calendar dates and historical grade revisions remain unverified.')]),
    ('Bayesian inference and numerical validation',[
        ('p','Standardize predictors and response using training data. In standardized units the prior is beta|sigma² ~ Normal(0, sigma² Lambda0^-1), with intercept precision 0.001 and slope precision 10; sigma² ~ InverseGamma(shape=2, scale=1). The posterior is Normal–Inverse-Gamma.'),
        ('code','L = Lambda0 + A.T @ A\nm = solve(L, A.T @ z)\na = 2 + n/2\nb = 1 + (z.T @ z - m.T @ L @ m)/2\nPredictive df = 2*a\nPredictive location = A_new @ m\nPredictive scale^2 = (b/a)*(1 + A_new @ inv(L) @ A_new.T)'),
        ('p','Independent simulation draws variance from IG(a,b) and coefficients from Normal(m, sigma² L^-1). The actual two-block Gibbs sampler alternates that coefficient draw with variance|beta,D ~ IG(a+p/2, b+(beta-m)ᵀL(beta-m)/2). Four dispersed chains each use 1,000 warmup and 4,000 retained iterations. Exact independent sampling uses 20,000 draws.'),
        ('table',(['Recorded numerical check','Result'],[
            ['Maximum rank-normalized split/folded R-hat',f'{chk["max_Rhat"]:.6f}'],['Minimum bulk ESS',f'{chk["min_bulk_ESS"]:,.0f}'],['Minimum tail ESS',f'{chk["min_tail_ESS"]:,.0f}'],['Largest posterior-mean error / MCSE',f'{chk["max_mean_error_in_MCSE"]:.3f}'],['Maximum simulated vs analytic risk-probability error',f'{chk["max_abs_risk_MC_error"]:.4f}']])),
        ('p','These results support computational correctness under the chosen model. MCMC is optional when a closed form exists. A Student-t predictive distribution arising from Gaussian likelihood plus parameter uncertainty is distinct from fitting a robust Student-t likelihood. No full missing-data DAG sampler, learned structure posterior, spike-and-slab inclusion probabilities or causal edge probabilities are claimed.'),
        ('p','Continuous shrinkage priors assign zero probability to an exactly zero coefficient. Therefore P(beta>0) is not a posterior edge-inclusion probability. If discrete inclusion probabilities are desired, they require an explicitly different model and sensitivity analysis.')]),
    ('Temporal source comparisons',[
        ('table',(['Train through','Evaluate','Evaluation students'],[['Winter 2025','Spring 2025','43'],['Spring 2025','Fall 2025','20'],['Fall 2025','Winter 2026','40'],['Winter 2026','Spring 2026','43']])),
        ('p','Every numeric comparison uses the same evaluation students. All eight subsets of LMS, EVC and wellness are tested under no grades, Block A and Block B: 96 main fits. Four sensitivity settings repeat the 96 fits (precision 1, precision 100, missingness indicators, complete non-grade respondents), giving 480 fits across main and sensitivity blocks. The final posterior interpretation also fits the earlier 148 students.'),
        ('p','Main precision 10 is inherited from the previously explored workflow. Its historical selection used some earlier-fold outcomes. These are explored temporal comparisons with overlapping training sets, not an unbiased independent confirmation estimate. When choosing new settings, inner earlier-term tuning must stay inside each training fold. Macro scores give each evaluation term equal weight; macro RMSE is an average of term RMSE values, not pooled RMSE.'),
        ('table',(['No-grades source','Macro MAE','MAE reduction','Terms improved'],[[a.extended,f'{e["macro"].query("context == \'No grades\'").set_index("group").loc[a.extended,"MAE"]:.3f}',f'{a.macro_MAE_gain:+.3f}',f'{a.terms_improved}/4'] for a in e['gains'].query("context == 'No grades' and comparison == 'add_to_baseline'").itertuples()])),
        ('p','LMS alone improves no-grades MAE from 6.5377 to 6.3607 (0.1770 points) and improves all four terms. LMS plus wellness improves by 0.1976, without establishing a distinct wellness contribution. EVC alone worsens all four term MAEs. All sources together improve only 0.0139 and are prior-sensitive. These no-grades scenarios do not establish an actual early prediction date.'),
        ('p','For Block B, the combined model worsens MAE in all four checks; average change is -0.0879 points of reduction. Adding individual groups and removing each from the full model is retained in paired_gain_summary.csv. Outcome-distribution metrics are mixed: full-model negative log density 2.7735 vs 2.7606 for grades only, coverage 91.1% vs 90.6%, width 12.08 vs 11.69, and Brier70 0.05891 vs 0.05910. This does not establish useful distributional improvement.')]),
    ('Factor sizes, predictive influence and risk',[
        ('p','Final Block B interpretation fit: 148 earlier students; one training standard deviation increase holding the other inputs and grades fixed. Units are final-percentage points, not questionnaire rating points and not intervention effects.'),
        ('table',(['Input','Mean points/SD','95% credible interval','P(positive)'],co_rows)),
        ('p','All six non-grade probabilities of an absolute conditional coefficient above one final-percentage point are below 1% under this prior and design. The intervals include zero. Conditioning on grades can block a pathway from motivation to performance; correlated inputs, measurement error, missingness and shrinkage also affect the estimates. These are not total causal effects.'),
        ('p','A separate prediction_shift_summary.csv distinguishes influence from utility. Adding all sources changes Block B predictions by roughly 0.31–0.50 points on average within the four evaluation terms, but those shifts do not reduce MAE. A source may affect an output without improving it.'),
        ('table',(['Reused Spring example','Mean','90% interval','P(final<70)','Actual'],[['Complete inputs','71.24','65.72–76.75','35.6%','75.95'],['Missing surveys; missed low result','77.60','71.36–83.83','2.3%','68.03'],['Extreme outcome; severity missed','45.91','39.33–52.49','~100%','20.01']])),
        ('p','The 70% threshold is illustrative, not an official pass/fail or intervention policy. The last two examples show model failure despite integrating parameter uncertainty. Missing inputs are still treated as fixed after filling, and rare low outcomes are too few for strong calibration claims. Training posterior-predictive checks of SD, minimum and counts below 70 fall within replicated ranges; that does not validate later-term low-outcome behavior. Predictions and intervals are unbounded Student-t distributions; only MAE/RMSE point predictions are clipped.')]),
    ('RETRO: newly supplied text and response behavior',[
        ('p','The upload has 870 rows, 290 student-week check-ins and 74 distinct students, all matching the grade table. Fifteen responses are blank and no student/week/question keys are duplicated. Only Fall 2025, Winter 2026 and Spring 2026 contain this instrument. Week 2/4 nonblank text gives 68 respondents: 13/20, 25/40 and 30/43. Exact timestamps are absent; Weeks 6/8/10 are excluded from the early-labelled scenario.'),
        ('p','Three separate train-only TF-IDF channels preserve the prompts: what went well, what did not go well and what could improve. Unigrams/bigrams use min_df=2 and at most 200 features per prompt; no/not/nor/never are retained. Response measures are whether a student responded, number of answers and weeks, and log word count. No external NLP service, numerical sentiment inference or validated psychological factor coding is used.'),
        ('p','Only two later-term checks are possible: Fall 2025 (20 students) trains the Winter 2026 test (40); Fall+Winter (60) trains the Spring 2026 test (43). The first model sees only 13 early text respondents. Ridge alpha 10 is the reference and alphas 1/100 are retained as sensitivity settings. All-student and respondent-only paired comparisons are exported. There are 108 fits across contexts, baselines, alphas and encodings.'),
        ('table',(['Evaluate','n','Grade-only MAE','Gain: response','Gain: text+response','Words over response'],rr)),
        ('p','In the Block B baseline scenario, text plus response improves Winter MAE by 0.3075 but worsens Spring by 0.0388. The mean gain is about 0.134 points, while response measures alone average about 0.200. The text content therefore has no consistent independent benefit in this scenario. Adding RETRO to all early numeric sources is also mixed. Other contexts and alpha values vary; selecting a favorable one would not establish a reliable effect.'),
        ('p','These scores cannot be compared directly with the earlier four-term 2.95/3.04 values: training windows and covered terms differ. A small sparse text model failing to help does not establish that reflections contain no useful information. Response measures may proxy engagement or selection. Raw responses are included for local reproducibility but are not quoted in the report or slides.')]),
    ('Candidate models and empirical diagnosis',[
        ('p','Five fixed model labels are compared on the same four numeric temporal checks and populations (120 fits). Bayesian CPD and standardized Ridge have the same point forecasts at the same slope penalty. They are not independent evidence for a discovery.'),
        ('table',(['Model','Block B grades-only MAE','Block B all-numeric MAE'],br)),
        ('p','Huber uses epsilon 1.35, alpha 1 and standardized outcomes; ExtraTrees uses 200 trees, depth 4 and minimum leaf 5; HistGB uses 150 iterations, seven leaves, min leaf 10, learning rate .05 and L2 10. Settings were not exhaustively tuned. This comparison is about point error, not posterior calibration of the alternatives.'),
        ('p','No tested replacement beats the simple larger-grades baseline. With no grades, Huber/ExtraTrees full-model MAEs around 6.42 slightly improve on Bayesian full-model 6.52, but do not beat the earlier Bayesian LMS-only MAE of 6.36. A more flexible model is not automatically preferable in 191 students.'),
        ('p','My diagnosis is that the current framework is a good exploratory capstone baseline: transparent assumptions, train-only preprocessing, temporal checks and quantifiable posterior uncertainty. It does not establish coaching effectiveness, causal paths, a verified early prediction time or robust low-outcome calibration. Grade-target part-whole dependence, missing surveys, six terms and unverified releases are more consequential than adding MCMC to an already tractable model.'),
        ('p','A regularized hierarchical term/section model, robust likelihood and explicit missing-data mechanisms are sensible candidates to test against the baseline if suitable longitudinal and context data are recovered. With six terms, priors and pooling variance would need sensitivity checks. Those models have not been fitted or shown superior here.')]),
    ('Grading weights, SMR policy and remaining-work accounting',[
        ('p','The user confirmed that the same category weights apply across the six historical non-summer terms. The main sum is 100%. Survey extra credit can add 0.75 final-percentage points and team-manager credit 0.25; MLC extra credit is weighted zero in this workbook. Do not renormalize the 101% combined weights. A zero grading weight is not a zero causal or educational effect.'),
        ('table',(['Main category','Weight'],wr)),
        ('p','The workbook inventory for course 84595 contains 126 items, 118 published. It includes unpublished versions alongside replacements: verbal category denominators are 183 vs 119 published points and 164 vs 100; teamwork 262 vs 246. Cached subtotals were verified against item rows. Neither all-inventory nor publication-only totals are automatically official historical effective denominators.'),
        ('p','Across 138 historical selected-assignment source rows, 116 match title and points but still lack verified historical group denominators; 12 have no exact current title match, six match an item unpublished in 84595, and four differ in point maximum. The workbook’s Fall 2026 due dates are not historical grade-release timestamps. Summer metadata is excluded before numeric/RETRO analyses and summer-labelled predictor columns are rejected. No existing row is removed and prior predictions were reproduced exactly.'),
        ('code','known assignment fraction = category_weight * assignment_points / category_total_points\nknown earned contribution = 100 * category_weight * earned_points / category_total_points\nfinal_total = known_contribution + (1-known_weight)*remaining_main_percent + extra_credit\nremaining_main_percent = (final_total-extra_credit-known_contribution)/(1-known_weight)'),
        ('p','The implementation requires an effective main-assignment catalog and actual timezone-aware score snapshots. It preserves students without grades, selects the latest state before cutoff, handles blank-score revocation, and rejects incomplete category rosters or unsupported excused/dropped adjustments. Extra credit must be supplied explicitly. Arithmetic round-trip tests pass. No real historical remaining-work targets or forecasting results are claimed.')]),
    ('Prioritized next study and what remains unavailable',[
        ('bullets',['Recover the original complete grade/source ZIP, historical effective assignment catalogs, unaggregated scores and extra-credit contributions.','Verify score release/revision snapshots and survey submission times; select one useful checkpoint. Due dates alone are insufficient.','Predict remaining coursework, then combine earned contribution and extra credit through deterministic grading rules.','Unroll feedback through time: earlier marks may affect later EVC/RETRO, which may predict later activity and marks. Retrospective descriptions are not automatically causes.','Validate EVC item wording/scoring and code RETRO themes such as workload, feedback, collaboration and study strategy with human agreement checks before giving them quantitative factor meanings.','Use observed prior preparation and term/section context where available; describe unmeasured confounding and response selection explicitly. A drawn latent node does not identify an effect.','If choosing new representations or tuning, use inner earlier-term validation. Test restrained pooling/robust/missing-data models against grades-only and LMS-only benchmarks.']),
        ('p','The current processed table aggregates assignments and early surveys. It cannot uniquely reconstruct full historical grading components, response trajectories or what was known by a particular date. Identical category weights do not solve these missing inputs. The original historical source ZIP is not included because it has not been supplied in this environment.'),
        ('p','The existing six terms are enough to finish an honest exploratory capstone. A new class would strengthen confirmation later, but is not a prerequisite for reporting these findings. A causal question about improving wellness or MLC coaching needs an explicit intervention/estimand and identification design beyond observational prediction.')]),
    ('Reproduction, verification and references',[
        ('p','The package includes four notebooks. MLC_Bayesian_DAG_updated.ipynb is the original supplied executed study and requires the missing original source ZIP for raw rerun. The three companion notebooks are executed: posterior/source value; RETRO/model follow-up; and weights/SMR audit. The current report supersedes the availability and status statements in earlier stage reports.'),
        ('code','cd 03_Project\npython3.12 -m venv .venv\n.venv/bin/python -m pip install -r requirements.txt\n.venv/bin/python -m unittest discover -s tests -v\n# To rerun all available studies after installation:\nbash run_available_studies.sh'),
        ('p','Core runs use existing pinned requirements; optional presentation/report dependencies are in posterior_study/requirements-presentation.txt. Python 3.12.14, seed 271828 and recorded hashes support reproduction. The release validation log is in 02_Report; MANIFEST.json records every shipped file hash. This package is a filesystem snapshot of current work, not a claim of a published environment or a Git push.'),
        ('p','Fourteen tests cover original outcome-CPD agreement, exact simulation, training-only preprocessing, detection of nonconverged chains, late-RETRO exclusion, duplicate/unmatched IDs, training-only text vocabulary, numeric benchmark reproduction, summer metadata/field exclusion, category-specific accounting, later-score exclusion, explicit extra-credit recombination, blank-score revocation and timezone/category completeness. Tests are executed from the packaged project.'),
        ('p','Method references: Murphy (2012), Machine Learning: A Probabilistic Perspective, Bayesian linear regression. Rubin (1981), The Bayesian Bootstrap, Annals of Statistics 9(1), 130–134, DOI 10.1214/aos/1176345338. Vehtari et al. (2021), Rank-Normalization, Folding, and Localization, Bayesian Analysis 16(2), 667–718, DOI 10.1214/20-BA1221. These support methods, not the empirical claims; no new remote literature review is claimed.'),
        ('p',f'Input SHA-256 values: processed table {e["prov"]["input_sha256"]}; RETRO {e["retro_prov"]["retro_sha256"]}; workbook {e["weight_prov"]["sha256"]}.')])]


def reports(dest,e,sections=None):
    dest.mkdir(parents=True,exist_ok=True);sections=report_sections(e) if sections is None else sections
    title=ParagraphStyle('title',fontName='MLCB',fontSize=18,leading=24,textColor=colors.HexColor(NAVY),spaceAfter=16)
    body=ParagraphStyle('body',fontName='MLC',fontSize=10,leading=15,textColor=colors.HexColor(NAVY),spaceAfter=10)
    cell=ParagraphStyle('cell',fontName='MLC',fontSize=8.4,leading=11,textColor=colors.HexColor(NAVY))
    head=ParagraphStyle('head',parent=cell,fontName='MLCB',textColor=colors.white)
    code=ParagraphStyle('code',fontName='Courier',fontSize=7.3,leading=10,backColor=colors.HexColor('#EAF0F8'),spaceAfter=12)
    flow=[];md=['# My Learning Coach — consolidated research report\n\nCurrent state: completed exploratory non-summer analyses, with supplied RETRO and grading weights.\n']
    for index,(name,blocks) in enumerate(sections,1):
        if index>1:flow.append(PageBreak())
        flow.append(Paragraph(f'{index}. {escape(name)}',title));md.append(f'## {index}. {name}\n')
        for kind,value in blocks:
            if kind=='p':flow.append(Paragraph(escape(value),body));md.append(value+'\n')
            elif kind=='bullets':
                for t in value:flow.append(Paragraph('• '+escape(t),body))
                md.append('\n'.join('- '+t for t in value)+'\n')
            elif kind=='code':
                # Long hashes/commands in paragraphs are wrapped; code is short.
                lines=[]
                for line in value.splitlines():
                    lines.extend([line[i:i+104] for i in range(0,len(line),104)] or [''])
                flow.append(Preformatted('\n'.join(lines),code));md.append('```text\n'+value+'\n```\n')
            elif kind=='table':
                headers,rows=value;n=len(headers)
                cells=[[Paragraph(escape(str(v)),head if j==0 else cell) for v in row] for j,row in enumerate([headers]+rows)]
                widths=[486/n]*n
                if n==2:widths=[345,141]
                if n==3:widths=[220,133,133]
                if n==4:widths=[170,100,124,92]
                if n==5:widths=[180,65,110,66,65]
                if n==6:widths=[75,25,85,96,110,95]
                t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F9'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5 if index==4 else 7),('BOTTOMPADDING',(0,0),(-1,-1),5 if index==4 else 7)]))
                flow += [t,Spacer(1,12)];md.append(mdtable(headers,rows)+'\n')
    def footer(c,doc):
        c.setFont('MLC',8);c.setFillColor(colors.HexColor(MUTED));c.drawString(54,30,'MLC · Consolidated report · Exploratory non-summer study');c.drawRightString(558,30,str(doc.page))
    SimpleDocTemplate(str(dest/'MLC_Consolidated_Report.pdf'),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=52,bottomMargin=52,title='My Learning Coach — consolidated research report').build(flow,onFirstPage=footer,onLaterPages=footer)
    (dest/'MLC_Consolidated_Report.md').write_text('\n'.join(md))


def diagrams(dest):
    dest.mkdir(parents=True,exist_ok=True)
    for suffix in ['svg','png','dot']:shutil.copy2(ROOT/f'mlc_results/expanded_full_DAG.{suffix}',dest/f'Original_Fitted_DAG.{suffix}')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
    fig,ax=plt.subplots(figsize=(13,4.5));ax.set_xlim(0,13);ax.set_ylim(0,4.5);ax.axis('off')
    ax.text(.3,4.1,'Proposed temporal prediction structure',fontsize=20,fontweight='bold',color=NAVY)
    ax.text(.3,3.6,'Hypotheses for a future study; not newly fitted or causally identified.',fontsize=11,color=MUTED)
    for x,title,text,c in [(.4,'Earlier marks','Observed performance\nat time t',TEAL),(4.7,'Later measurements','EVC / wellness / RETRO\nat time t+1',PURPLE),(9.,'Future coursework','Activity and new marks\nat time t+2',NAVY)]:
        ax.add_patch(FancyBboxPatch((x,1.65),3.5,1.25,boxstyle='round,pad=.1',facecolor=c,edgecolor='none'))
        ax.text(x+.18,2.52,title,color='white',fontsize=14,fontweight='bold');ax.text(x+.18,1.98,text,color='white',fontsize=11)
    for a,b in [(3.95,4.5),(8.25,8.8)]:ax.add_patch(FancyArrowPatch((a,2.25),(b,2.25),arrowstyle='-|>',mutation_scale=20,color=MUTED,lw=2))
    ax.text(.4,.7,'Use actual timestamps; separate earned marks from remaining coursework.',fontsize=12,color=TEAL)
    ax.text(.4,.2,'Validate measurement and response selection; add observed prior preparation and context where available.',fontsize=10,color=MUTED)
    fig.tight_layout()
    for fmt in ['png','svg']:fig.savefig(dest/f'Proposed_Temporal_Structure.{fmt}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    (dest/'README.md').write_text('# Diagrams\n\nOriginal_Fitted_DAG is the original 23-node, 62-edge fixed graph. It is not a causal discovery result.\n\nProposed_Temporal_Structure is a labelled research proposal, not an estimated replacement graph. See the consolidated report for missing-data and timing limitations.\n')


def copy_project(dest,include_inputs=True):
    dest.mkdir(parents=True,exist_ok=True)
    ignore=shutil.ignore_patterns('__pycache__','*.pyc','.ipynb_checkpoints')
    for name in ['posterior_study','tests','mlc_results','posterior_results','retro_followup_results','grading_results']:
        shutil.copytree(ROOT/name,dest/name,ignore=ignore)
    for name in ['MLC_Bayesian_DAG_updated.ipynb','MLC_Posterior_Predictive_Value.ipynb','MLC_RETRO_Followup.ipynb','MLC_Weights_SMR_Audit.ipynb','requirements.txt','.gitignore']:
        shutil.copy2(ROOT/name,dest/name)
    data=dest/'data';data.mkdir()
    for name in (['retro_uploaded.csv','assignment_weights_uploaded.xlsx'] if include_inputs else []):
        if not (ROOT/'data'/name).exists():raise FileNotFoundError(f'Required supplied input missing: {name}')
        shutil.copy2(ROOT/'data'/name,data/name)
    (data/'README.md').write_text('# Included inputs\n\nretro_uploaded.csv is the supplied anonymized RETRO file. assignment_weights_uploaded.xlsx is the supplied category-weight/assignment workbook. The copied files are byte-for-byte originals; hashes are in provenance and the release manifest.\n\nThe 191-row processed table is ../mlc_results/expanded_student_features.csv. The original historical Annoymized Data ZIP and complete release/revision snapshots were not supplied and are not included.\n')
    (dest/'README.md').write_text('''# Runnable My Learning Coach project

Start with ../00_START_HERE.md and the current report in ../02_Report/. Earlier presentations/reports are in ../05_Archive/.

## Notebook order

1. MLC_Bayesian_DAG_updated.ipynb — original supplied executed study. Raw rerun requires the missing historical source ZIP.
2. MLC_Posterior_Predictive_Value.ipynb — executed posterior simulation, actual Gibbs MCMC and four-term source ablations.
3. MLC_RETRO_Followup.ipynb — executed display of RETRO audit, text comparisons and candidate-model results.
4. MLC_Weights_SMR_Audit.ipynb — executed weight/summer audit and a clearly labelled arithmetic example.

## Install and run

Use the existing isolated checkout if working in Codex; do not create a worktree unless explicitly requested. For an extracted local package:

```bash
cd 03_Project
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run_available_studies.sh
```

The script reruns the studies supported by the included inputs and the tests. It does not invoke the raw original notebook or claim that missing history has been reconstructed. It writes the existing result folders. Optional editable presentation/PDF generation requires:

```bash
.venv/bin/python -m pip install -r posterior_study/requirements-presentation.txt
.venv/bin/python -m posterior_study.create_release --output /path/to/a/new/release
```

The release target must be new/empty and outside this project root. Included supplied inputs are in data/; the processed table and original results are in mlc_results/. No external API keys are needed. Graphviz is optional for the original graph workflow. Use the .venv kernel for notebooks.

## Module map

- analysis.py — fixed-design NIG posterior, direct simulation, Gibbs, diagnostics, source ablations.
- retro_followup.py — RETRO matching/week filtering, train-only text, candidate models.
- grading_weights.py — workbook extraction, mapping audit and remaining-work arithmetic.
- cohort_policy.py — explicit Summer/SMR metadata/field exclusion.
- create_release.py — current integrated presentation, report, guides and package.
- Other report/build modules recreate the earlier stage artifacts for traceability.

The all-student comparison uses train-only median filling and differs from the original joint-Gaussian missing-evidence method. RETRO is open text, not the early numerical EVC instrument. Category weights are confirmed; effective historical denominators and score-availability snapshots remain missing. No causal or remaining-work forecasting result is claimed.
''')
    runner='''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Create .venv with Python 3.12 and install requirements.txt first." >&2
  exit 1
fi
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export MPLCONFIGDIR="${TMPDIR:-/tmp}/mlc-matplotlib"
export JUPYTER_RUNTIME_DIR="${TMPDIR:-/tmp}/mlc-jupyter"
export IPYTHONDIR="${TMPDIR:-/tmp}/mlc-ipython"
.venv/bin/python -m posterior_study.analysis
.venv/bin/python -m posterior_study.retro_followup --retro-csv data/retro_uploaded.csv
.venv/bin/python -m posterior_study.grading_weights --weights-xlsx data/assignment_weights_uploaded.xlsx
.venv/bin/python -m unittest discover -s tests -v
'''
    (dest/'run_available_studies.sh').write_text(runner);(dest/'run_available_studies.sh').chmod(0o755)


def archive(dest,references):
    dest.mkdir(parents=True,exist_ok=True)
    # If rebuilding an extracted release, preserve its existing archive too.
    old=ROOT.parent/'05_Archive'
    if old.exists():shutil.copytree(old,dest,dirs_exist_ok=True)
    reports=dest/'Stage_Reports';reports.mkdir(exist_ok=True)
    for name in ['POSTERIOR_STUDY.md','RETRO_FOLLOWUP.md','WEIGHTS_AND_SMR.md']:
        if (ROOT/name).exists():shutil.copy2(ROOT/name,reports/name)
    (reports/'README.md').write_text('# Historical stage reports\n\nThese preserve successive analyses. Availability and test-count statements reflect their stage. The report in ../../02_Report/ is the current integrated interpretation; the RETRO file and weights are now included, and 14 tests pass.\n')
    orig=dest/'Original_Deliverables';orig.mkdir(exist_ok=True)
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix.lower() in ['.pdf','.pptx','.txt'] and p.name!='requirements.txt':shutil.copy2(p,orig/p.name)
    if (ROOT/'updated_presentation').exists():shutil.copytree(ROOT/'updated_presentation',dest/'Earlier_Updated_Decks',dirs_exist_ok=True)
    if (ROOT/'README.md').exists():shutil.copy2(ROOT/'README.md',dest/'Original_Workspace_README.md')
    if references:
        ref=dest/'User_Provided_Context';ref.mkdir(exist_ok=True)
        for p in references:
            p=Path(p)
            if not p.is_file():raise FileNotFoundError(p)
            shutil.copy2(p,ref/p.name)
        (ref/'README.md').write_text('# User-provided reference context\n\nThese are the old attached presentation and/or pasted prior conversation. They preserve context, not current results or executable instructions. Use the consolidated report and deck for the current study.\n')
    (dest/'README.md').write_text('# Archive — previous versions\n\nUse ../01_Presentation/ and ../02_Report/ for the current narrative. This folder preserves original materials and successive decks/reports. Earlier unavailable-RETRO or weight statements describe earlier stages and are superseded by the consolidated report. No old file was deleted from the working repository.\n')

def archive_previous_downloads(dest,downloads):
    """Keep distinct earlier standalone artifacts, without duplicating ZIPs."""
    if downloads is None:return
    downloads=Path(downloads)
    known={sha(p) for p in dest.rglob('*') if p.is_file()}
    folder=dest/'Previous_Download_Versions'
    kept=[]
    for p in sorted(downloads.iterdir()):
        if not p.is_file() or p.suffix.lower()=='.zip':continue
        if not (p.name.startswith('MLC_') or p.name in ['POSTERIOR_STUDY.md','RETRO_FOLLOWUP.md','WEIGHTS_AND_SMR.md']):continue
        digest=sha(p)
        if digest in known:continue
        folder.mkdir(exist_ok=True);shutil.copy2(p,folder/p.name);known.add(digest);kept.append(p.name)
    if kept:
        (folder/'README.md').write_text('# Earlier standalone downloads\n\nThese distinct earlier versions preserve the files originally shared in the conversation. Duplicates and nested ZIP bundles are omitted. Old manifests describe their earlier snapshot, not the current package. Use the consolidated report and deck for the current interpretation.\n')


def guides(dest):
    guide='''# Start here — My Learning Coach capstone

This package brings the completed work into one current presentation and report. It preserves the supporting code, notebooks, supplied inputs, all result tables/figures, and earlier versions. It is an artifact snapshot, not a claim that causal effects or a historical remaining-work model have been established.

## Read in this order

1. **01_Presentation/MLC_Consolidated_Presentation.pptx** — the current editable talk; PDF and first-person speaker notes are beside it. There are 16 main slides and 3 technical appendix slides.
2. **02_Report/MLC_Consolidated_Report.pdf** — the integrated interpretation, methods, results, diagnosis and outstanding inputs; Markdown is also supplied.
3. **03_Project/README.md** — notebook order, installation and rerun commands. Code, tests and evidence stay together so relative paths work.
4. **04_Diagrams/** — full original graph and a clearly labelled proposed temporal structure.
5. **05_Archive/** — original and intermediate decks/reports. Historical availability statements there are superseded by the current report.

## What the evidence currently says

- Main data: 191 unique students, six Fall/Winter/Spring terms; SMR/Summer excluded.
- Adding all numeric non-grade sources to Block B increased macro MAE from 2.9485 to 3.0364 points.
- Without grades, LMS alone improved macro MAE from 6.5377 to 6.3607, across all four checks.
- Coefficients describe uncertain conditional associations; they do not establish causal or coaching effects.
- RETRO is newly supplied open text, not the early numerical EVC scale. Its two-term content gains are mixed and do not consistently beat response-pattern measures.
- The tested Huber and tree alternatives do not beat the simple larger-grades Bayesian/Ridge baseline.
- Main grading weights total 100%, with up to 1 extra-credit point. The same weights were confirmed for the historical non-summer terms.
- Remaining-work arithmetic is implemented/tested. A real historical remaining-work model is not fitted.

## Included inputs and missing history

Included under 03_Project/data/: the supplied anonymized RETRO CSV and assignment/weight XLSX. The 191-row processed table is in 03_Project/mlc_results/. The four notebooks and all generated result folders are included.

**Still missing:** the original historical source ZIP/complete grade exports, effective historical assignment denominators and verified score-release/revision snapshots. Final-export aggregates plus the weights cannot uniquely recover that history. The original raw-data notebook therefore cannot be fully rerun from this package alone.

## Verification and navigation

Fourteen tests are run from the packaged project. See 02_Report/Validation_Log.txt and Validation.json. All notebook files are structurally validated; the original notebook's stored execution is preserved rather than falsely reported as a new raw rerun. Per-run provenance and input hashes live beside each result set. MANIFEST.json hashes every shipped file; 02_Report/Artifact_Index.csv is the machine-readable file inventory. Open INDEX.html for clickable navigation.

The standalone PDFs use the same line wrapping/layout specification as the editable deck. Statistical plots are embedded high-resolution images; slide text and diagrams are native editable objects. The full graph is also available as SVG/PNG/DOT.
'''
    (dest/'00_START_HERE.md').write_text(guide)
    (dest/'03_Project'/'NOTEBOOK_ORDER.md').write_text('''# Notebook order and execution status

| Order | File | Purpose | Reproduction status |
|---|---|---|---|
| 1 | MLC_Bayesian_DAG_updated.ipynb | Original fixed DAG, extraction and original results | Stored original execution preserved; raw rerun needs the missing historical ZIP |
| 2 | MLC_Posterior_Predictive_Value.ipynb | Posterior simulation, Gibbs and source ablations | Executed companion notebook; processed input is included |
| 3 | MLC_RETRO_Followup.ipynb | RETRO audit/text and candidate models | Executed result-display notebook; rerun commands and raw RETRO input included |
| 4 | MLC_Weights_SMR_Audit.ipynb | Category weights, exclusion and arithmetic example | Executed; hypothetical example is labelled, not a real remaining-work target |

Use the integrated report in ../02_Report/ for the latest combined interpretation. Different experiments have different training windows: four numeric evaluation terms versus two RETRO terms. Do not combine their MAEs as if they were one test set.
''')


def validate(dest):
    import os,sys,nbformat
    project=dest/'03_Project';report=dest/'02_Report'
    env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='2';env['OMP_NUM_THREADS']='2';env['MPLCONFIGDIR']='/tmp/mlc-release-matplotlib'
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=project,env=env,capture_output=True,text=True,timeout=120)
    (report/'Validation_Log.txt').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('Packaged-project tests failed; inspect Validation_Log.txt')
    if 'Ran 14 tests' not in result.stderr or 'OK' not in result.stderr:raise RuntimeError('Expected fourteen executed tests')
    notebooks={}
    for path in sorted(project.glob('*.ipynb')):
        n=nbformat.read(path,as_version=4);nbformat.validate(n);cs=[c for c in n.cells if c.cell_type=='code']
        errors=[o for c in cs for o in c.get('outputs',[]) if o.output_type=='error']
        if errors:raise ValueError(f'Notebook contains saved errors: {path.name}')
        notebooks[path.name]={'code_cells':len(cs),'saved_executed_cells':sum(c.get('execution_count') is not None for c in cs),'validated_structure':True,'raw_original_rerun':False if path.name=='MLC_Bayesian_DAG_updated.ipynb' else None}
    ppt=Presentation(dest/'01_Presentation/MLC_Consolidated_Presentation.pptx')
    if len(ppt.slides)!=19:raise ValueError('Expected 19 consolidated slides')
    for i,slide in enumerate(ppt.slides,1):
        if not slide.notes_slide.notes_text_frame.text.strip():raise ValueError(f'Missing notes slide {i}')
        for sh in slide.shapes:
            if sh.has_text_frame and (sh.left<0 or sh.top<0 or sh.left+sh.width>ppt.slide_width+100 or sh.top+sh.height>ppt.slide_height+100):raise ValueError(f'Text shape outside slide {i}')
    # Confirm packaged supplied inputs match their audited source hashes.
    if sha(project/'data/retro_uploaded.csv')!=json.loads((project/'retro_followup_results/retro_provenance.json').read_text())['retro_sha256']:raise ValueError('RETRO hash mismatch')
    if sha(project/'data/assignment_weights_uploaded.xlsx')!=json.loads((project/'grading_results/weight_audit.json').read_text())['sha256']:raise ValueError('Workbook hash mismatch')
    for p in sorted(project.rglob('__pycache__'),reverse=True):shutil.rmtree(p)
    result_meta={'tests_executed':14,'tests_passed':14,'test_exit_code':result.returncode,'test_working_directory':'03_Project','notebooks':notebooks,'consolidated_slides':len(ppt.slides),'all_slides_have_notes':True,'provided_input_hashes_verified':True,'original_raw_workflow_rerun':False,'remaining_work_model_fitted':False,'publication_or_git_push_performed':False}
    (report/'Validation.json').write_text(json.dumps(result_meta,indent=2))
    return result_meta


def render_previews(dest):
    if not shutil.which('pdftoppm'):raise RuntimeError('pdftoppm is needed to review slide rendering')
    tmp=dest/'01_Presentation'/'_rendered_review';tmp.mkdir()
    subprocess.run(['pdftoppm','-scale-to','1000','-png',str(dest/'01_Presentation/MLC_Consolidated_Presentation.pdf'),str(tmp/'slide')],check=True,capture_output=True,timeout=120)
    files=sorted(tmp.glob('slide-*.png'))
    if len(files)!=19:raise ValueError('PDF rendering did not produce 19 slides')
    width=1600;cellw=400;cellh=250;rows=(len(files)+3)//4
    canvas_img=PILImage.new('RGB',(width,rows*cellh),'#DCE3ED');draw=ImageDraw.Draw(canvas_img)
    for i,path in enumerate(files):
        im=PILImage.open(path);im.thumbnail((390,220));x=i%4*cellw;y=i//4*cellh;canvas_img.paste(im,(x,y));draw.text((x+10,y+225),f'Slide {i+1}',fill='black')
    canvas_img.save(dest/'01_Presentation/Slide_Overview.png')
    shutil.copy2(files[0],dest/'01_Presentation/Title_Slide.png')
    # Keep review renders until human/model visual inspection; excluded from the
    # index/package by cleanup_review after that inspection is complete.
    return tmp


def index_and_manifest(dest,validation):
    report=dest/'02_Report'
    for p in [report/'Artifact_Index.csv',report/'Artifact_Index.md',dest/'INDEX.html']:p.touch()
    paths=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '_rendered_review' not in p.parts)
    rows=[]
    for p in paths:
        rel=p.relative_to(dest).as_posix();top=rel.split('/')[0]
        stage='archive' if top=='05_Archive' else 'current'
        if top=='03_Project' and p.name=='MLC_Bayesian_DAG_updated.ipynb':stage='original baseline; stored execution'
        role={'01_Presentation':'Current talk and speaker notes','02_Report':'Current report, inventory and validation','03_Project':'Runnable notebooks, source, tests, inputs and complete results','04_Diagrams':'Original graph / labelled proposal','05_Archive':'Earlier versions / user reference context'}.get(top,'Entry guide / navigation')
        rows.append({'path':rel,'status':stage,'role':role,'extension':p.suffix.lower()})
    with (report/'Artifact_Index.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['path','status','role','extension']);writer.writeheader();writer.writerows(rows)
    (report/'Artifact_Index.md').write_text('# Complete artifact index\n\n'+mdtable(['Path','Status','Role'],[[a['path'],a['status'],a['role']] for a in rows])+'\n')
    quick=[('Start here','00_START_HERE.md'),('Current PowerPoint','01_Presentation/MLC_Consolidated_Presentation.pptx'),('Current slide PDF','01_Presentation/MLC_Consolidated_Presentation.pdf'),('Research report PDF','02_Report/MLC_Consolidated_Report.pdf'),('Speaker notes PDF','01_Presentation/Speaker_Notes.pdf'),('Slide overview','01_Presentation/Slide_Overview.png'),('Project run guide','03_Project/README.md'),('Four-notebook guide','03_Project/NOTEBOOK_ORDER.md'),('Original DAG (SVG)','04_Diagrams/Original_Fitted_DAG.svg'),('Validation','02_Report/Validation.json')]
    links=''.join(f'<a href="{html.escape(path,quote=True)}">{html.escape(name)}</a>' for name,path in quick)
    listing=''.join(f'<tr><td><a href="{html.escape(a["path"],quote=True)}">{html.escape(a["path"])}</a></td><td>{html.escape(a["status"])}</td><td>{html.escape(a["role"])}</td></tr>' for a in rows)
    doc='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MLC — artifact guide</title><style>body{font:16px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 24px;color:#15273f;background:#f6f8fc}h1{font-size:36px}.links{display:flex;gap:12px;flex-wrap:wrap}.links a{padding:12px 16px;border-radius:8px;background:#fff;color:#0f766e;text-decoration:none;border:1px solid #dce3ed}.note{background:#fff1de;border-radius:8px;padding:18px;margin:24px 0}table{width:100%;border-collapse:collapse;background:white;font-size:13px}th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #dce3ed}th{background:#15273f;color:white}a{color:#2563eb}code{background:#eaf0f8;padding:2px 5px}img{max-width:100%;border-radius:8px}input{padding:12px;width:min(700px,90%);font-size:16px;border:1px solid #b6c4d6;border-radius:6px}</style><h1>My Learning Coach</h1><p>One current research package: consolidated findings, reproducible project, supplied inputs and labelled archives.</p><div class="links">'''+links+'''</div><div class="note"><strong>Study scope:</strong> exploratory conditional prediction; causal effects are not established. SMR/Summer excluded. Weighted remaining-work arithmetic is tested, but a historical remaining-work model is not fitted. The original historical source ZIP and verified score-availability history are still missing.</div><p><strong>Verification:</strong> 14 tests passed from the packaged project; four notebooks validated; 19 slides with first-person notes. Open this page after unzipping so relative links resolve.</p><img src="01_Presentation/Title_Slide.png" alt="Consolidated presentation title slide"><h2>All artifacts</h2><p><input id="filter" aria-label="Filter artifact paths" placeholder="Filter by filename, folder or status"></p><table><thead><tr><th>Path</th><th>Status</th><th>Purpose</th></tr></thead><tbody>'''+listing+'''</tbody></table><script>document.getElementById('filter').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});</script></html>'''
    (dest/'INDEX.html').write_text(doc)
    files={p.relative_to(dest).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}
    manifest={'package':'My Learning Coach consolidated current artifact snapshot','local_date':'2026-11-12','timezone':'America/Los_Angeles','file_count':len(files),'validation':validation,'files':files,'manifest_self_hash':'excluded to avoid recursive hashing'}
    (dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    return len(files)


def build(dest,references=(),previous_downloads=None):
    dest=Path(dest).resolve()
    if dest==ROOT.resolve() or ROOT.resolve() in dest.parents:raise ValueError('Release must be outside source project root')
    if dest.exists() and any(dest.iterdir()):raise ValueError('Choose a new or empty release directory; existing files are preserved')
    dest.mkdir(parents=True,exist_ok=True)
    register_fonts();e=evidence()
    copy_project(dest/'03_Project');archive(dest/'05_Archive',references);archive_previous_downloads(dest/'05_Archive',previous_downloads);guides(dest)
    slides=presentation(dest/'01_Presentation',e);reports(dest/'02_Report',e);diagrams(dest/'04_Diagrams')
    validation=validate(dest)
    render_previews(dest)
    # The preview PNGs are reviewed separately. Individual review renders are
    # temporary and not part of the delivered inventory; overview is retained.
    n=index_and_manifest(dest,validation)
    print(json.dumps({'release_path':str(dest),'slides':slides,'tests_passed':14,'files':n,'review_images':str(dest/'01_Presentation/_rendered_review')},indent=2))
    return dest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--reference',type=Path,action='append',default=[]);parser.add_argument('--previous-downloads',type=Path)
    args=parser.parse_args();build(args.output,args.reference,args.previous_downloads)
