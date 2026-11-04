"""Geometric, continuously animated Manim film for Stewart chapter 15.

All vectors and equations are editable Mobjects. No slide screenshots are used.
"""
from pathlib import Path
import os, json, hashlib, re
ROOT=Path(__file__).resolve().parent
os.environ['XDG_CACHE_HOME']=str(ROOT.parent/'.cache')
os.environ['MPLCONFIGDIR']=str(ROOT.parent/'.cache/matplotlib-v2')
os.environ['TMPDIR']=str(ROOT.parent/'.cache')
from manim import *
import numpy as np
from contextlib import contextmanager

INK='#0c0f14'; SKY='#75c8ff'; MINT='#67d9bd'; SUN='#ffdb7d'; CORAL='#ff8497'; DIM='#617184'; WHITE='#e9edf4'
config.background_color=INK
config.max_files_cached=500

def M(*parts,colors=None,size=1):
    """Computer Modern SVG equations; native vector paths, with stable scale."""
    from matplotlib.mathtext import math_to_image, MathTextParser
    from matplotlib.font_manager import FontProperties
    folder=ROOT/'media/equations';folder.mkdir(exist_ok=True,parents=True)
    objects=[];offset=0
    for i,s in enumerate(parts):
        s=re.sub(r'\\frac(\d)(\d)',r'\\frac{\1}{\2}',s)
        p=folder/(hashlib.sha256(s.encode()).hexdigest()[:18]+'.svg')
        if not p.exists(): math_to_image('$'+s+'$',str(p),prop=FontProperties(size=40,math_fontfamily='cm'),format='svg',color=WHITE)
        header=p.read_text()
        # Matplotlib writes an opaque figure background; equations need only ink.
        clean=re.sub(r'<g id="patch_1">.*?</g>','',header,flags=re.S)
        if clean!=header:p.write_text(clean)
        h=float(re.search(r'height="([\d.]+)pt',header)[1])
        ob=SVGMobject(str(p),height=h*.015*size,fill_color=WHITE,fill_opacity=1,stroke_width=0)
        metrics=MathTextParser('path').parse('$'+s+'$',dpi=72,prop=FontProperties(size=40,math_fontfamily='cm'))
        ob.move_to([offset+ob.width/2,(h/2-metrics.depth)*.015*size,0]);offset+=ob.width+.12
        if colors and i<len(colors) and colors[i]:ob.set_color(colors[i])
        objects.append(ob)
    group=VGroup(*objects).move_to(ORIGIN)
    if group.width>12.2:group.scale_to_fit_width(12.2)
    return group

def T(s,size=30,color=WHITE):return Text(s,font='DejaVu Sans',font_size=size,color=color,weight=NORMAL)
def footer(*parts,colors=None):return M(*parts,colors=colors).to_edge(DOWN,buff=.38)
def tag(s):return T(s,22,DIM).to_corner(UL,buff=.35)
def plane():
    p=Axes(x_range=[0,1.15,.25],y_range=[0,1.15,.25],x_length=5.2,y_length=4.2,axis_config={'color':DIM,'include_tip':True,'include_ticks':False}).shift(LEFT*2.4+UP*.35)
    return p
def path(points,**kw):return VMobject(**kw).set_points_as_corners(points)
def face(points,color=SKY,opacity=.6):return Polygon(*points,fill_color=color,fill_opacity=opacity,stroke_color=color,stroke_width=1)
def tangent_arrow(start,end,color):
    direction=end-start;direction=direction/np.linalg.norm(direction)
    normal=np.array([-.8,-.8,1.0]);normal=normal/np.linalg.norm(normal)
    side=np.cross(normal,direction);side=side/np.linalg.norm(side)
    tip=face([end,end-.17*direction+.07*side,end-.17*direction-.07*side],color,1)
    return VGroup(Line(start,end,color=color,stroke_width=5),tip)

class Narration:
    @contextmanager
    def beat(self,key):
        scene=self.__class__.__name__; identifier=f'{scene}_{key}'
        durations=json.loads((ROOT/'audio/durations.json').read_text())
        length=durations[identifier]+.35; start=float(self.renderer.time)
        if not hasattr(self,'cue_log'):self.cue_log=[]
        self.cue_log.append({'scene':scene,'key':key,'start':start,'duration':length})
        self.add_sound(str(ROOT/'audio'/f'{identifier}.mp3'))
        yield length
        remaining=start+length-float(self.renderer.time)
        if remaining>0:self.wait(remaining)
        if os.environ.get('FILM_STILLS'):
            folder=ROOT/'previews';folder.mkdir(exist_ok=True,parents=True)
            self.renderer.update_frame(self)
            self.renderer.camera.get_image().save(folder/f'{identifier}.png')
    def finish(self):
        folder=ROOT/'media/cues';folder.mkdir(exist_ok=True,parents=True)
        (folder/f'{self.__class__.__name__}.json').write_text(json.dumps(self.cue_log,indent=2))
        self.play(*[FadeOut(m) for m in list(self.mobjects)],run_time=.7)

class Flat(Narration,MovingCameraScene):
    def heading(self,s):
        h=tag(s);self.play(FadeIn(h),run_time=.6);return h

class Space(Narration,ThreeDScene):
    def fixed(self,m):
        self.add_fixed_in_frame_mobjects(m);self.remove(m);return m
    def setup_space(self,title,axes=None,phi=65,theta=-50,zoom=.84):
        self.set_camera_orientation(phi=phi*DEGREES,theta=theta*DEGREES,zoom=zoom)
        if axes is None:axes=ThreeDAxes(x_range=[0,2,1],y_range=[0,2,1],z_range=[0,2,1],x_length=4.7,y_length=4.7,z_length=3.5,axis_config={'color':DIM,'include_ticks':False,'include_tip':False})
        self.axes=axes
        h=self.fixed(tag(title));self.play(Create(axes),FadeIn(h),run_time=1)
        self.begin_ambient_camera_rotation(rate=.025)
        return axes,h
    def wire(self,f,xmax=2,ymax=2):
        a=self.axes;g=VGroup()
        for u in np.linspace(0,xmax,17):
            g.add(ParametricFunction(lambda v,u=u:a.c2p(u,v,f(u,v)),t_range=[0,ymax,.035],color=SKY,stroke_width=1.3))
        for v in np.linspace(0,ymax,17):
            g.add(ParametricFunction(lambda u,v=v:a.c2p(u,v,f(u,v)),t_range=[0,xmax,.035],color=MINT,stroke_width=1.3))
        return g
    def column(self,x,y,dx,dy,h,color=SKY):
        a=self.axes
        return Prism(dimensions=[dx*2.35,dy*2.35,max(.01,h*1.75)],fill_color=color,fill_opacity=.72,stroke_color=INK,stroke_width=.5).move_to(a.c2p(x+dx/2,y+dy/2,h/2))

class Volume(Space):
    def construct(self):
        a,title=self.setup_space('15.1   /   BUILDING A DOUBLE INTEGRAL')
        f=lambda x,y:1.45-.17*(x-.5)**2-.18*(y-.8)**2
        roof=self.wire(f)
        with self.beat('question') as d:
            self.play(LaggedStart(*[Create(c) for c in roof],lag_ratio=.025),run_time=d*.55)
            q=self.fixed(T('How much space is under this roof?',34).to_edge(DOWN,buff=.55));self.play(FadeIn(q,shift=UP*.15),run_time=1.5)
        x,y,delta=.9,.35,.28
        tile=face([a.c2p(x,y,0),a.c2p(x+delta,y,0),a.c2p(x+delta,y+delta,0),a.c2p(x,y+delta,0)],SUN,1)
        col=self.column(x,y,delta,delta,f(x+delta/2,y+delta/2),SUN)
        with self.beat('tile') as d:
            self.play(FadeOut(q),roof.animate.set_stroke(opacity=.28),FadeIn(tile),run_time=1.5)
            self.play(TransformFromCopy(tile,col),run_time=d*.45)
            self.move_camera(phi=72*DEGREES,theta=-65*DEGREES,zoom=1.05,run_time=2)
        formula=self.fixed(footer(r'\Delta V',r'\approx',r'f(x,y)',r'\Delta x\,\Delta y',colors=[SUN,WHITE,SKY,MINT]))
        with self.beat('product') as d:
            self.play(Write(formula[0]),Write(formula[1]),run_time=1)
            height=Line(a.c2p(x,y,0),a.c2p(x,y,f(x,y)),color=SKY,stroke_width=6)
            self.play(Create(height),Write(formula[2]),run_time=2)
            self.play(tile.animate.set_color(MINT),Write(formula[3]),run_time=2)
            self.play(Indicate(col,color=SUN),run_time=2)
        def columns(n):return VGroup(*[self.column(i*2/n,j*2/n,2/n,2/n,f((i+.5)*2/n,(j+.5)*2/n),interpolate_color(BLUE_D,ManimColor(MINT),(i+j)/(2*n))) for j in range(n) for i in range(n)])
        blocks=columns(5)
        total=self.fixed(footer(r'\sum_{i,j}',r'f(x_i,y_j)',r'\Delta A',colors=[SUN,SKY,MINT]))
        with self.beat('assemble') as d:
            self.play(FadeOut(height),FadeOut(tile),FadeOut(col),roof.animate.set_stroke(opacity=.65),run_time=1)
            self.play(LaggedStart(*[GrowFromEdge(b,IN) for b in blocks],lag_ratio=.035),run_time=d*.55)
            self.play(ReplacementTransform(formula,total),run_time=1.8)
        with self.beat('refine') as d:
            finer=columns(9);finest=columns(14)
            self.play(ReplacementTransform(blocks,finer),run_time=d*.3)
            self.move_camera(phi=68*DEGREES,theta=-34*DEGREES,zoom=.95,run_time=d*.2)
            self.play(ReplacementTransform(finer,finest),run_time=d*.3)
        result=self.fixed(footer(r'\iint_D',r'f(x,y)',r'dA',colors=[SUN,SKY,MINT]))
        with self.beat('integral') as d:
            self.play(ReplacementTransform(total,result),finest.animate.set_opacity(.3),roof.animate.set_stroke(opacity=1),run_time=3)
            self.move_camera(phi=58*DEGREES,theta=-74*DEGREES,run_time=d*.5)
        self.finish()

class Slices(Space):
    def construct(self):
        a,title=self.setup_space('15.1   /   ADD A SLICE, THEN ADD THE SLICES')
        old=a
        a=ThreeDAxes(x_range=[0,2,1],y_range=[0,1,.5],z_range=[0,3,1],x_length=4.7,y_length=2.35,z_length=3.5,axis_config={'color':DIM,'include_ticks':False,'include_tip':False})
        self.remove(old);self.add(a);self.axes=a
        f=lambda x,y:x+y
        roof=self.wire(f,xmax=2,ymax=1);self.add(roof)
        t=ValueTracker(.15)
        def slice_x(x):return face([a.c2p(x,0,0),a.c2p(x,1,0)]+[a.c2p(x,y,f(x,y)) for y in np.linspace(1,0,30)],SUN,.58)
        sl=always_redraw(lambda:slice_x(t.get_value()))
        with self.beat('row') as d:
            self.play(roof.animate.set_stroke(opacity=.4),FadeIn(sl),run_time=2)
            self.play(t.animate.set_value(1.25),run_time=d*.6,rate_func=smooth)
        inner=self.fixed(footer(r'A(x)=',r'\int_c^d f(x,y)\,dy',colors=[SUN,SKY]))
        with self.beat('inner') as d:
            self.play(Write(inner),run_time=2)
            self.play(t.animate.set_value(.3),run_time=d*.35)
            self.play(t.animate.set_value(1.7),run_time=d*.35)
        stack=VGroup(*[slice_x(x).set_opacity(.22) for x in np.linspace(.1,1.9,18)])
        outer=self.fixed(footer(r'V=',r'\int_a^b',r'\left[\int_c^d f(x,y)\,dy\right]',r'dx',colors=[WHITE,MINT,SKY,MINT]))
        with self.beat('outer') as d:
            self.play(t.animate.set_value(.05),run_time=1)
            self.play(LaggedStart(*[FadeIn(s) for s in stack],lag_ratio=.1),t.animate.set_value(1.95),run_time=d*.65)
            self.play(ReplacementTransform(inner,outer),run_time=2)
        with self.beat('switch') as d:
            other=VGroup(*[face([a.c2p(0,y,0),a.c2p(2,y,0),a.c2p(2,y,f(2,y)),a.c2p(0,y,f(0,y))],MINT,.3) for y in np.linspace(.05,.95,18)])
            self.play(FadeOut(sl),ReplacementTransform(stack,other),run_time=3)
            fub=self.fixed(footer(r'\int_a^b\!\int_c^d f\,dy\,dx',r'=',r'\int_c^d\!\int_a^b f\,dx\,dy',colors=[SKY,WHITE,MINT]))
            self.play(ReplacementTransform(outer,fub),run_time=2)
            self.move_camera(theta=-25*DEGREES,run_time=d*.4)
        with self.beat('example') as d:
            example=self.fixed(footer(r'\int_0^2\!\int_0^1(x+y)\,dy\,dx',r'=',r'\int_0^2(x+\frac12)\,dx',r'=3',colors=[SKY,WHITE,MINT,SUN]))
            # Mathtext requires explicit braces in fractions.
            self.play(ReplacementTransform(fub,example),run_time=3)
            self.play(Indicate(example[-1],color=SUN),run_time=2)
        self.finish()

class Bounds(Flat):
    def construct(self):
        h=self.heading('15.2   /   THE BOUNDS ARE A PICTURE')
        a=plane(); x=np.linspace(0,1,100)
        low=a.plot(lambda x:x*x,x_range=[0,1],color=SKY);high=a.plot(lambda x:x,x_range=[0,1],color=MINT)
        region=face([a.c2p(v,v*v) for v in x]+[a.c2p(v,v) for v in x[::-1]],SKY,.18)
        l1=M('y=x^2',colors=[SKY],size=.8).next_to(a.c2p(.9,.81),RIGHT);l2=M('y=x',colors=[MINT],size=.8).next_to(a.c2p(.5,.5),UL)
        with self.beat('curves') as d:
            self.play(Create(a),Create(low),run_time=2.5);self.play(Create(high),FadeIn(l1),FadeIn(l2),run_time=2)
            self.play(FadeIn(region),run_time=2)
        v=ValueTracker(.02)
        scan=always_redraw(lambda:Line(a.c2p(v.get_value(),v.get_value()**2),a.c2p(v.get_value(),v.get_value()),color=SUN,stroke_width=8))
        ends=always_redraw(lambda:VGroup(Dot(a.c2p(v.get_value(),v.get_value()**2),color=SKY,radius=.06),Dot(a.c2p(v.get_value(),v.get_value()),color=MINT,radius=.06)))
        with self.beat('vertical') as d:
            self.add(scan,ends);self.play(v.animate.set_value(.98),run_time=d*.8,rate_func=linear)
        eq=VGroup(M(r'0\leq x\leq1',colors=[SUN]),M(r'x^2\leq y\leq x',colors=[SKY])).arrange(DOWN,buff=.5).move_to(RIGHT*3.5+UP*.5)
        with self.beat('write') as d:
            self.play(v.animate.set_value(.55),run_time=1.5)
            self.play(Write(eq[0]),run_time=2);self.play(Write(eq[1]),run_time=2)
            integral=footer(r'\int_0^1',r'\int_{x^2}^{x}',r'f(x,y)\,dy\,dx',colors=[SUN,SKY,WHITE]);self.play(Write(integral),run_time=2)
        y=ValueTracker(.02)
        horizontal=always_redraw(lambda:Line(a.c2p(y.get_value(),y.get_value()),a.c2p(np.sqrt(y.get_value()),y.get_value()),color=CORAL,stroke_width=8))
        with self.beat('horizontal') as d:
            self.play(FadeOut(scan),FadeOut(ends),FadeOut(eq),FadeIn(horizontal),run_time=1.5)
            self.play(y.animate.set_value(.98),run_time=d*.65,rate_func=linear)
        with self.beat('reverse') as d:
            eq2=VGroup(M(r'0\leq y\leq1',colors=[CORAL]),M(r'y\leq x\leq\sqrt{y}',colors=[MINT])).arrange(DOWN,buff=.5).move_to(RIGHT*3.5+UP*.5)
            self.play(y.animate.set_value(.4),Write(eq2),run_time=3)
            reverse=footer(r'\int_0^1',r'\int_y^{\sqrt{y}}',r'f(x,y)\,dx\,dy',colors=[CORAL,MINT,WHITE]);self.play(ReplacementTransform(integral,reverse),run_time=2.5)
            self.play(Indicate(region,color=SUN),run_time=2)
        with self.beat('area') as d:
            result=footer(r'A=\int_0^1(x-x^2)\,dx',r'=\frac16',colors=[SKY,SUN]);self.play(ReplacementTransform(reverse,result),run_time=2.5)
            self.play(y.animate.set_value(.01),run_time=2);self.play(y.animate.set_value(.99),run_time=d*.35)
        self.finish()

class Polar(Flat):
    def construct(self):
        h=self.heading('15.3   /   WHY THE EXTRA r?')
        center=LEFT*2.6+UP*.3; scale=2.05
        def polar(r,t):return center+scale*r*np.array([np.cos(t),np.sin(t),0])
        # Parameter domain rectangle unwraps into a full polar grid, tile by tile.
        nr,nt=8,24; grid=VGroup(); target=VGroup()
        for j in range(nt):
            for i in range(nr):
                r0,r1=i/nr,(i+1)/nr;t0,t1=TAU*j/nt,TAU*(j+1)/nt
                points=[np.array([-5+3*r,-2+4*t/TAU,0]) for r,t in [(r0,t0),(r1,t0),(r1,t1),(r0,t1)]]
                grid.add(face(points,interpolate_color(ManimColor(SKY),ManimColor(MINT),i/nr),.15))
                aa=np.linspace(t0,t1,5); pts=[polar(r1,t) for t in aa]+[polar(r0,t) for t in aa[::-1]]
                target.add(face(pts,interpolate_color(ManimColor(SKY),ManimColor(MINT),i/nr),.16))
        with self.beat('grid') as d:
            self.play(LaggedStart(*[FadeIn(g) for g in grid],lag_ratio=.003),run_time=3)
            self.play(Transform(grid,target),run_time=d*.48)
        r=ValueTracker(.6);theta=.35;dr=.16;dt=.22
        def patch():
            aa=np.linspace(theta,theta+dt,15);rr=r.get_value()
            return face([polar(rr+dr,t) for t in aa]+[polar(rr,t) for t in aa[::-1]],SUN,.95)
        tile=always_redraw(patch)
        # An enlarged exact annular tile, not a decorative quadrilateral.
        def enlarged_tile():
            rr=r.get_value();angles=np.linspace(-dt/2,dt/2,30)
            points=[np.array([3+12*(rr+dr)*np.sin(a),.4+12*((rr+dr)*np.cos(a)-(rr+dr/2)),0]) for a in angles]
            points += [np.array([3+12*rr*np.sin(a),.4+12*(rr*np.cos(a)-(rr+dr/2)),0]) for a in angles[::-1]]
            return face(points,SUN,.3)
        big=always_redraw(enlarged_tile)
        with self.beat('tile') as d:
            self.play(grid.animate.set_opacity(.3),FadeIn(tile),run_time=2)
            self.play(TransformFromCopy(tile,big),run_time=2.5)
            radial=M('dr',colors=[MINT]).next_to(big,RIGHT);arc=M(r'r\,d\theta',colors=[SUN]).next_to(big,UP)
            radial.add_updater(lambda m:m.next_to(big,RIGHT));arc.add_updater(lambda m:m.next_to(big,UP))
            self.play(Write(radial),Write(arc),run_time=2)
        radius=always_redraw(lambda:Line(center,polar(r.get_value(),theta),color=SKY,stroke_width=3))
        with self.beat('stretch') as d:
            self.play(Create(radius),run_time=1)
            self.play(r.animate.set_value(.2),run_time=2)
            self.play(r.animate.set_value(.83),run_time=d*.5)
        factor=footer(r'dA=',r'dr',r'\times',r'r\,d\theta',r'=r\,dr\,d\theta',colors=[WHITE,MINT,WHITE,SUN,SUN])
        with self.beat('factor') as d:
            self.play(TransformFromCopy(radial,factor[1]),TransformFromCopy(arc,factor[3]),Write(factor[0]),Write(factor[2]),run_time=2.5)
            self.play(Write(factor[4]),run_time=2);self.play(Indicate(factor[4],color=SUN),run_time=2)
        with self.beat('dome') as d:
            self.play(FadeOut(big),FadeOut(radial),FadeOut(arc),FadeOut(radius),FadeOut(tile),run_time=1)
            height=M(r'1-x^2-y^2',r'\longrightarrow',r'1-r^2',colors=[SKY,WHITE,MINT]).move_to(RIGHT*2.9+UP*.7)
            bounds=M(r'0\leq r\leq1,',r'\quad0\leq\theta\leq2\pi',colors=[MINT,SKY],size=.75).next_to(height,DOWN,buff=.5)
            self.play(Write(height),grid.animate.set_stroke(opacity=.6).set_fill(opacity=.12),run_time=3);self.play(Write(bounds),run_time=2)
        with self.beat('compute') as d:
            calculation=footer(r'\int_0^{2\pi}\!\int_0^1',r'(1-r^2)',r'r\,dr\,d\theta',r'=\frac{\pi}{2}',colors=[WHITE,MINT,SUN,SUN])
            self.play(FadeOut(factor),Write(calculation[:3]),run_time=3)
            self.play(Write(calculation[3]),run_time=2);self.play(Circumscribe(calculation[3],color=SUN),run_time=2)
        self.finish()

class Density(Flat):
    def construct(self):
        h=self.heading('15.4   /   WHAT DOES EACH PIECE CARRY?')
        cells=VGroup(*[Square(.23,stroke_width=.3,stroke_color=INK,fill_color=interpolate_color(ManimColor('#18405d'),ManimColor(MINT),i/15),fill_opacity=1).move_to([-4+i*.23,-1.8+j*.23,0]) for j in range(16) for i in range(16)])
        with self.beat('sheet') as d:
            self.play(LaggedStart(*[FadeIn(c) for c in cells],lag_ratio=.003),run_time=4)
            density=M(r'\delta(x,y)=1+x',colors=[MINT]).move_to(RIGHT*3+UP*.8);self.play(Write(density),run_time=2)
        dm=M(r'dm=',r'\delta(x,y)',r'dA',colors=[WHITE,MINT,SKY]).move_to(RIGHT*3+DOWN*.3)
        mass=footer(r'm=\iint_D',r'\delta(x,y)',r'dA',colors=[WHITE,MINT,SKY])
        with self.beat('mass') as d:
            self.play(Indicate(cells[180],color=SUN),Write(dm),run_time=2.5)
            self.play(Write(mass),run_time=2);self.play(LaggedStart(*[Indicate(cells[i],scale_factor=1.15,color=SUN) for i in range(0,256,21)],lag_ratio=.15),run_time=3)
        cx=-4+15*.23*5/9;cy=-1.8+15*.23/2;balance=Dot([cx,cy,0],radius=.085,color=SUN)
        with self.beat('balance') as d:
            self.play(FadeOut(dm),FadeOut(density),run_time=1)
            dots=VGroup(*[Dot(c.get_center(),radius=.025+.025*(i%16)/15,color=SUN) for i,c in enumerate(cells) if i%3==0])
            self.play(FadeIn(dots),run_time=1)
            self.play(*[dot.animate.move_to(balance.get_center()).set_opacity(.15) for dot in dots],run_time=4)
            self.play(FadeOut(dots),FadeIn(balance),run_time=1)
            center=M(r'\bar{x}=\frac{\iint_D x\delta\,dA}{m}',colors=[SUN],size=.9).move_to(RIGHT*3+UP*.3);self.play(Write(center),run_time=2)
        with self.beat('result') as d:
            result=footer(r'm=\frac{3}{2},',r'\qquad(\bar{x},\bar{y})=\left(\frac{5}{9},\frac{1}{2}\right)',colors=[MINT,SUN]);self.play(ReplacementTransform(mass,result),run_time=2)
            symmetry=DashedLine([-4,cy,0],[-.55,cy,0],color=WHITE,stroke_width=2);self.play(Create(symmetry),Flash(balance,color=SUN),run_time=2)
        with self.beat('applications') as d:
            applications=VGroup(M(r'f_{\rm avg}=\frac{1}{A(D)}\iint_D f\,dA',colors=[SKY],size=.72),M(r'I_y=\iint_D x^2\delta\,dA',colors=[MINT],size=.72),M(r'P(D)=\iint_D p\,dA',colors=[CORAL],size=.72)).arrange(DOWN,buff=.55).move_to(RIGHT*3+UP*.4)
            self.play(FadeOut(center),run_time=.6)
            for ob in applications:self.play(Write(ob),run_time=2)
        self.finish()

class SurfaceArea(Space):
    def construct(self):
        # Equal physical scales make the surface-area multiplier visible.
        axes=ThreeDAxes(x_range=[0,1,.5],y_range=[0,1,.5],z_range=[0,2,1],x_length=3,y_length=3,z_length=6,axis_config={'color':DIM,'include_ticks':False,'include_tip':False})
        a,title=self.setup_space('15.5   /   THE PATCH AND ITS SHADOW',axes=axes,phi=60,theta=-130,zoom=.60)
        tilt=ValueTracker(.05)
        grid=self.wire(lambda x,y:0,xmax=1,ymax=1)
        base_points=[curve.get_points().copy() for curve in grid]
        origin=a.c2p(0,0,0);last=[None]
        def lift_grid(m):
            value=tilt.get_value()
            if last[0]==value:return
            last[0]=value
            for curve,base in zip(m,base_points):
                points=base.copy()
                points[:,2]+=value*((points[:,0]-origin[0])+(points[:,1]-origin[1]))
                curve.set_points(points)
        grid.add_updater(lift_grid)
        shadow=face([a.c2p(.3,.3,0),a.c2p(.6,.3,0),a.c2p(.6,.6,0),a.c2p(.3,.6,0)],SKY,.8)
        patch=always_redraw(lambda:face([a.c2p(x,y,tilt.get_value()*(x+y)) for x,y in [(.3,.3),(.6,.3),(.6,.6),(.3,.6)]],SUN,.9))
        with self.beat('shadow') as d:
            self.play(FadeIn(grid),FadeIn(shadow),FadeIn(patch),run_time=2)
            self.play(tilt.animate.set_value(.55),run_time=d*.55)
        with self.beat('tilt') as d:
            connectors=always_redraw(lambda:VGroup(*[DashedLine(a.c2p(x,y,0),a.c2p(x,y,tilt.get_value()*(x+y)),color=DIM,stroke_width=1) for x,y in [(.3,.3),(.6,.3),(.6,.6),(.3,.6)]]))
            self.add(connectors);self.play(tilt.animate.set_value(.05),run_time=3)
            self.play(tilt.animate.set_value(.8),run_time=d*.5)
        with self.beat('edges') as d:
            start=a.c2p(.3,.3,.48)
            u=tangent_arrow(start,a.c2p(.6,.3,.72),MINT);v=tangent_arrow(start,a.c2p(.3,.6,.72),CORAL)
            self.play(Create(u),Create(v),run_time=3)
            vectors=self.fixed(footer(r'(1,0,f_x)',r'\times',r'(0,1,f_y)',r'=(-f_x,-f_y,1)',colors=[MINT,WHITE,CORAL,SUN]))
            self.play(Write(vectors),run_time=3)
        with self.beat('factor') as d:
            area=self.fixed(footer(r'dS=',r'\sqrt{1+f_x^2+f_y^2}',r'dA',colors=[WHITE,SUN,SKY]));self.play(ReplacementTransform(vectors,area),run_time=2.5)
            self.move_camera(phi=55*DEGREES,theta=-130*DEGREES,run_time=d*.45)
        with self.beat('example') as d:
            example=self.fixed(footer(r'z=x+y:',r'\quad A=\int_0^1\!\int_0^1\sqrt{3}\,dy\,dx',r'=\sqrt{3}',colors=[WHITE,SKY,SUN]));self.play(ReplacementTransform(area,example),FadeOut(u),FadeOut(v),tilt.animate.set_value(1),run_time=3)
            self.move_camera(phi=60*DEGREES,theta=-110*DEGREES,run_time=d*.5)
        self.finish()

class Solids(Space):
    def construct(self):
        a,title=self.setup_space('15.6–15.7   /   FILLING SPACE')
        cubes=VGroup(*[self.column(x,y,.22,.22,.22,interpolate_color(ManimColor(SKY),ManimColor(MINT),z)).shift(OUT*z*1.75) for z in [0,.25,.5,.75] for y in [0,.25,.5,.75] for x in [0,.25,.5,.75]])
        with self.beat('boxes') as d:
            self.play(LaggedStart(*[FadeIn(c,shift=OUT*.3) for c in cubes],lag_ratio=.018),run_time=d*.55)
            dv=self.fixed(footer(r'dV=',r'dx',r'dy',r'dz',colors=[WHITE,SKY,MINT,CORAL]));self.play(Write(dv),run_time=2)
        v=[a.c2p(0,0,0),a.c2p(1,0,0),a.c2p(0,1,0),a.c2p(0,0,1)]
        tetra=VGroup(*[face([v[k] for k in inds],SKY,.22) for inds in [(0,1,2),(0,1,3),(0,2,3),(1,2,3)]]).scale(1.65,about_point=a.c2p(0,0,0))
        # The diagram scale changes uniformly; coordinates retain unit intercepts.
        def p(x,y,z):return a.c2p(0,0,0)+1.65*(a.c2p(x,y,z)-a.c2p(0,0,0))
        q=ValueTracker(.12)
        column=always_redraw(lambda:Line(p(q.get_value(),.2,0),p(q.get_value(),.2,.8-q.get_value()),color=SUN,stroke_width=8))
        with self.beat('tetra') as d:
            self.play(FadeOut(cubes),FadeIn(tetra),FadeIn(column),run_time=3)
            self.play(q.animate.set_value(.67),run_time=d*.5)
        with self.beat('bounds') as d:
            bounds=self.fixed(footer(r'\int_0^1',r'\int_0^{1-x}',r'\int_0^{1-x-y}',r'1\,dz\,dy\,dx',colors=[SKY,MINT,SUN,WHITE]));self.play(ReplacementTransform(dv,bounds),run_time=3)
            self.play(q.animate.set_value(.08),run_time=3)
            shadow=face([p(0,0,0),p(1,0,0),p(0,1,0)],MINT,.5);self.play(FadeIn(shadow),run_time=2)
        with self.beat('volume') as d:
            evaluation=self.fixed(footer(r'\int_0^1\!\int_0^{1-x}(1-x-y)\,dy\,dx',r'=\int_0^1\frac{(1-x)^2}{2}\,dx',r'=\frac16',colors=[SUN,MINT,SKY]));self.play(ReplacementTransform(bounds,evaluation),run_time=3)
            self.move_camera(theta=-15*DEGREES,run_time=d*.45)
        with self.beat('cylinder') as d:
            self.play(FadeOut(tetra),FadeOut(column),FadeOut(shadow),FadeOut(evaluation),run_time=1)
            rings=VGroup(*[ParametricFunction(lambda t,z=z:a.c2p(.8+.75*np.cos(t),.8+.75*np.sin(t),z),t_range=[0,TAU,.04],color=MINT,stroke_width=2) for z in np.linspace(0,1.8,15)])
            self.play(LaggedStart(*[Create(r) for r in rings],lag_ratio=.15),run_time=d*.45)
            cylinder=self.fixed(footer(r'dV=',r'r\,dr\,d\theta',r'dz',colors=[WHITE,SUN,CORAL]));self.play(Write(cylinder),run_time=2)
        self.finish()

class Spherical(Space):
    def construct(self):
        self.set_camera_orientation(phi=66*DEGREES,theta=-38*DEGREES,zoom=.9)
        self.begin_ambient_camera_rotation(rate=.025)
        title=self.fixed(tag('15.8   /   THREE LENGTHS ON A SPHERICAL SHELL'));self.add(title)
        R=2.1
        def p(r,ph,th):return r*np.array([np.sin(ph)*np.cos(th),np.sin(ph)*np.sin(th),np.cos(ph)])
        lines=VGroup()
        for ph in np.linspace(.15,PI-.15,15):lines.add(ParametricFunction(lambda t,ph=ph:p(R,ph,t),t_range=[0,TAU,.045],color=SKY,stroke_width=1))
        for th in np.linspace(0,TAU,24,endpoint=False):lines.add(ParametricFunction(lambda t,th=th:p(R,t,th),t_range=[0,PI,.035],color=MINT,stroke_width=1))
        ph=ValueTracker(1);th=-.7
        radial=always_redraw(lambda:Line(ORIGIN,p(R,ph.get_value(),th),color=SUN,stroke_width=4))
        with self.beat('ball') as d:
            self.play(LaggedStart(*[Create(c) for c in lines],lag_ratio=.015),run_time=4)
            self.play(Create(radial),run_time=2)
            coordinates=self.fixed(footer(r'\rho:\ \mathrm{distance}',r'\quad\theta:\ \mathrm{around}',r'\quad\phi:\ \mathrm{down\ from}\ +z',colors=[SUN,SKY,MINT]));self.play(Write(coordinates),run_time=2.5)
        dp,dt,dr=.24,.28,.32
        def block():
            phi=ph.get_value();corners=[(phi,th),(phi+dp,th),(phi+dp,th+dt),(phi,th+dt)]
            return VGroup(face([p(R,f,t) for f,t in corners],SUN,.5),face([p(R+dr,f,t) for f,t in corners],SUN,.7),*[Line(p(R,f,t),p(R+dr,f,t),color=CORAL,stroke_width=3) for f,t in corners])
        patch=always_redraw(block)
        with self.beat('block') as d:
            self.play(lines.animate.set_stroke(opacity=.25),FadeIn(patch),FadeOut(coordinates),run_time=2)
            self.move_camera(phi=72*DEGREES,theta=-60*DEGREES,zoom=1.05,run_time=3)
            lengths=self.fixed(footer(r'd\rho',r'\qquad\rho\,d\phi',colors=[CORAL,MINT]));self.play(Write(lengths),run_time=2)
        latitude=always_redraw(lambda:ParametricFunction(lambda t:p(R,ph.get_value(),t),t_range=[0,TAU,.03],color=SKY,stroke_width=3))
        with self.beat('latitude') as d:
            self.add(latitude);self.play(ph.animate.set_value(.18),run_time=4)
            self.play(ph.animate.set_value(PI/2),run_time=4)
            third=self.fixed(footer(r'd\rho',r'\quad\rho\,d\phi',r'\quad\rho\sin\phi\,d\theta',colors=[CORAL,MINT,SKY]));self.play(ReplacementTransform(lengths,third),run_time=2)
        with self.beat('multiply') as d:
            result=self.fixed(footer(r'dV=',r'd\rho',r'(\rho\,d\phi)',r'(\rho\sin\phi\,d\theta)',r'=\rho^2\sin\phi\,d\rho\,d\phi\,d\theta',colors=[WHITE,CORAL,MINT,SKY,SUN]));self.play(ReplacementTransform(third,result),run_time=3)
            self.play(ph.animate.set_value(.6),run_time=3);self.play(ph.animate.set_value(1.3),run_time=3)
        with self.beat('check') as d:
            check=self.fixed(footer(r'\int_0^{2\pi}\!\int_0^\pi\!\int_0^a\rho^2\sin\phi\,d\rho\,d\phi\,d\theta',r'=\frac{4\pi a^3}{3}',colors=[WHITE,SUN]));self.play(ReplacementTransform(result,check),run_time=3)
            self.move_camera(phi=58*DEGREES,theta=-30*DEGREES,zoom=.85,run_time=d*.5)
        self.finish()

class Jacobian(Flat):
    def construct(self):
        h=self.heading('15.9   /   THE LOCAL EXCHANGE RATE FOR AREA')
        grid=NumberPlane(x_range=[-2,2,.4],y_range=[-2,2,.4],x_length=5,y_length=5,background_line_style={'stroke_color':SKY,'stroke_width':1,'stroke_opacity':.5},axis_config={'stroke_opacity':.3}).shift(LEFT*3)
        def warp(p):
            x,y,z=p+RIGHT*3
            return np.array([x+.18*y*y+3,y+.2*np.sin(x*1.2),z])
        target=grid.copy().prepare_for_nonlinear_transform();target.apply_function(warp)
        with self.beat('warp') as d:
            self.play(Create(grid),run_time=3)
            copy=grid.copy();self.add(copy);self.play(Transform(copy,target),run_time=d*.5)
        small=Square(.65,color=SUN,fill_opacity=.3).move_to(LEFT*3+UP*.5)
        mapped=small.copy().apply_function(warp)
        with self.beat('zoom') as d:
            self.play(grid.animate.set_stroke(opacity=.25).set_fill(opacity=0),copy.animate.set_stroke(opacity=.25).set_fill(opacity=0),FadeIn(small),run_time=2)
            self.play(TransformFromCopy(small,mapped),run_time=3)
            self.camera.frame.save_state()
            self.play(self.camera.frame.animate.scale(.8).move_to(RIGHT*.2),run_time=2)
        with self.beat('det') as d:
            a=mapped.get_vertices();u=Arrow(a[0],a[1],buff=0,color=MINT);v=Arrow(a[0],a[3],buff=0,color=CORAL)
            self.play(GrowArrow(u),GrowArrow(v),run_time=2)
            jac=footer(r'J=x_u y_v-x_v y_u,',r'\qquad dA=|J|\,du\,dv',colors=[SUN,SKY]);self.play(Restore(self.camera.frame),Write(jac),run_time=3)
        with self.beat('ellipse') as d:
            self.play(FadeOut(grid),FadeOut(copy),FadeOut(small),FadeOut(mapped),FadeOut(u),FadeOut(v),run_time=1)
            disk=Circle(1.5,color=SKY,fill_opacity=.2).shift(LEFT*3.2)
            tiling=VGroup(*[Line([-1.5,y,0],[1.5,y,0],color=SKY,stroke_width=1).shift(LEFT*3.2) for y in np.linspace(-1.4,1.4,12)])
            # Clip chords to the disk so the map visibly preserves its domain.
            tiling=VGroup(*[Line([-np.sqrt(2.25-y*y),y,0],[np.sqrt(2.25-y*y),y,0],color=SKY,stroke_width=1).shift(LEFT*3.2) for y in np.linspace(-1.4,1.4,12)])
            ellipse=VGroup(disk.copy(),tiling.copy()).stretch(1.6,0).move_to(RIGHT*3)
            self.play(Create(disk),Create(tiling),run_time=2)
            # The visual horizontal factor is exactly two; fit both into frame.
            ellipse=VGroup(disk.copy(),tiling.copy()).stretch(2,0).move_to(RIGHT*3)
            self.play(TransformFromCopy(VGroup(disk,tiling),ellipse),run_time=3)
            area=footer(r'x=2u,\ y=v,',r'\quad |J|=2,',r'\quad A=2\pi',colors=[WHITE,SUN,MINT]);self.play(ReplacementTransform(jac,area),run_time=2)
        with self.beat('rule') as d:
            rule=footer(r'\iint_D f(x,y)\,dx\,dy',r'=',r'\iint_S f(x(u,v),y(u,v))\,|J|\,du\,dv',colors=[SKY,WHITE,MINT]);self.play(ReplacementTransform(area,rule),run_time=3)
            self.play(Indicate(ellipse,color=SUN),run_time=2)
        with self.beat('ending') as d:
            self.play(*[FadeOut(m) for m in [disk,tiling,ellipse,rule,h]],run_time=1.5)
            words=VGroup(T('Draw the pieces.',42,SKY),T('Measure their size.',42,MINT),T('Add what they contribute.',42,SUN)).arrange(DOWN,buff=.6)
            self.play(LaggedStart(*[FadeIn(w,shift=UP*.2) for w in words],lag_ratio=.6),run_time=4)
            closing=M(r'\mathrm{total}=\int\mathrm{local\ contribution}',colors=[WHITE]).next_to(words,DOWN,buff=.8);self.play(Write(closing),run_time=2)
        self.finish()
