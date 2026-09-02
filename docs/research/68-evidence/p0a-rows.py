import time, os, sys, hashlib, subprocess, json, tempfile
from pathlib import Path
T0=time.time()
import OCP
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Vec, gp_Trsf
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_SOLID
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_ListOfShape, TopTools_FormatVersion
from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Compound
from OCP.BRep import BRep_Tool, BRep_Builder
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape, HLRBRep_PolyAlgo, HLRBRep_PolyHLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs, STEPControl_Controller
from OCP.STEPCAFControl import STEPCAFControl_Writer, STEPCAFControl_Reader
from OCP.Interface import Interface_Static
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.XCAFApp import XCAFApp_Application
from OCP.TDataStd import TDataStd_Name
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.TDF import TDF_LabelSequence
OUT = Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
OUT.mkdir(exist_ok=True)
def nunique(s, kind):
    m = TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s, kind, m); return m.Extent()
def vol(s):
    p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); return p.Mass()
def box(x,y,z,at=(0,0,0)): return BRepPrimAPI_MakeBox(gp_Pnt(*at), x,y,z).Shape()
def cyl(r,h,at,d=(0,0,1)): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*at), gp_Dir(*d)), r, h).Shape()
def nary_cut(base, tools):
    op = BRepAlgoAPI_Cut(); a=TopTools_ListOfShape(); a.Append(base); t=TopTools_ListOfShape()
    for s in tools: t.Append(s)
    op.SetArguments(a); op.SetTools(t); op.SetRunParallel(True); op.Build(); return op
def unify(s):
    u = ShapeUpgrade_UnifySameDomain(s, True, True, False); u.Build(); return u.Shape()
def edges_of(s):
    ex=TopExp_Explorer(s, TopAbs_EDGE); out=[]
    m = TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s, TopAbs_EDGE, m)
    return [TopoDS.Edge_s(m.FindKey(i)) for i in range(1, m.Extent()+1)]
def fp(shape):
    faces=[]; m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(shape, TopAbs_FACE, m)
    for i in range(1, m.Extent()+1):
        f=TopoDS.Face_s(m.FindKey(i)); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); c=p.CentreOfMass()
        faces.append((round(p.Mass(),3), round(c.X(),3), round(c.Y(),3), round(c.Z(),3)))
    faces.sort(); return hashlib.sha256(repr(faces).encode()).hexdigest()[:16]
def hlr_counts(shape, d, poly=False):
    proj = HLRAlgo_Projector(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(*d)))
    t=time.time()
    if poly:
        BRepMesh_IncrementalMesh(shape, 0.1, False, 0.5, True)
        algo = HLRBRep_PolyAlgo(); algo.Load(shape); algo.Projector(proj); algo.Update()
        h = HLRBRep_PolyHLRToShape(); h.Update(algo)
        names = ['VCompound','Rg1LineVCompound','OutLineVCompound','HCompound','Rg1LineHCompound','OutLineHCompound']
    else:
        algo = HLRBRep_Algo(); algo.Add(shape); algo.Projector(proj); algo.Update(); algo.Hide()
        h = HLRBRep_HLRToShape(algo)
        names = ['VCompound','Rg1LineVCompound','OutLineVCompound','HCompound','Rg1LineHCompound','OutLineHCompound']
    dt=time.time()-t
    counts={}
    for n in names:
        c = getattr(h, n)()
        counts[n] = 0 if c.IsNull() else nunique(c, TopAbs_EDGE)
    return dt, counts
R = {}
# ---- fixtures
F1 = BRepAlgoAPI_Cut(box(100,60,10), cyl(5,12,(50,30,-1))).Shape()
R['F1'] = dict(vol=round(vol(F1),3), faces=nunique(F1,TopAbs_FACE), edges=nunique(F1,TopAbs_EDGE))
# F2 bracket
t=time.time()
f2 = BRepAlgoAPI_Fuse(box(80,60,6), box(80,6,34,(0,0,6))).Shape(); f2=unify(f2)
# inner fillet r6 on the edge at y=6,z=6 along x
mk = BRepFilletAPI_MakeFillet(f2)
for e in edges_of(f2):
    c=BRepAdaptor_Curve(e)
    if c.GetType()==GeomAbs_Line:
        p1=c.Value(c.FirstParameter()); p2=c.Value(c.LastParameter())
        if abs(p1.Y()-6)<1e-6 and abs(p2.Y()-6)<1e-6 and abs(p1.Z()-6)<1e-6 and abs(p2.Z()-6)<1e-6: mk.Add(6.0, e)
f2 = mk.Shape()
holes=[cyl(3.3, 8, (x,y,-1)) for x,y in [(20,30),(60,30),(20,50),(60,50)]]
f2 = nary_cut(f2, holes).Shape()
R['F2'] = dict(vol=round(vol(f2),3), faces=nunique(f2,TopAbs_FACE), edges=nunique(f2,TopAbs_EDGE), build_s=round(time.time()-t,3), fp=fp(f2))
# F5
t=time.time(); plate=box(220,220,12); tools=[cyl(4,14,(20+20*i,20+20*j,-1)) for i in range(10) for j in range(10)]
op=nary_cut(plate, tools); F5=op.Shape(); R['F5']=dict(vol=round(vol(F5),3), faces=nunique(F5,TopAbs_FACE), edges=nunique(F5,TopAbs_EDGE), nary_s=round(time.time()-t,3))
# F6
blk = BRepAlgoAPI_Cut(box(40,40,20), cyl(5,22,(20,20,-1))).Shape(); pin = cyl(5,40,(20,20,-10))
R['F6'] = dict(block=round(vol(blk),3), pin=round(vol(pin),3), fp_block=fp(blk), fp_pin=fp(pin))
pin11 = cyl(5.5,40,(20,20,-10)); R['F6']['interf_d11']=round(vol(BRepAlgoAPI_Common(blk,pin11).Shape()),3)
# ---- row 8: HLR per compound
for name,d in [('front',(0,-1,0)),('top',(0,0,-1)),('right',(1,0,0))]:
    dt,c = hlr_counts(F1,d); R[f'F1_hlr_{name}']=dict(ms=round(dt*1000,1), **c)
# W3 plate 120x80x10, 12 holes d6, fillet ALL edges r1
w3 = nary_cut(box(120,80,10), [cyl(3,12,(15+30*i, 20+20*j, -1)) for i in range(4) for j in range(3)]).Shape()
mk = BRepFilletAPI_MakeFillet(w3)
for e in edges_of(w3): mk.Add(1.0, e)
mk.Build(); w3f = mk.Shape(); R['W3plate']=dict(faces=nunique(w3f,TopAbs_FACE), fillet_done=mk.IsDone())
dt,c = hlr_counts(w3f,(0,-1,0)); R['W3plate_hlr_front']=dict(ms=round(dt*1000,1), **c)
# 5xF5 stacked: exact vs poly
comp=TopoDS_Compound(); bb=BRep_Builder(); bb.MakeCompound(comp)
for k in range(5):
    tr=gp_Trsf(); tr.SetTranslation(gp_Vec(0,0,30*k)); bb.Add(comp, BRepBuilderAPI_Transform(F5, tr, True).Shape())
dt,c=hlr_counts(comp,(0,-1,0)); R['5xF5_exact']=dict(faces=nunique(comp,TopAbs_FACE), ms=round(dt*1000,1), **c)
dt,c=hlr_counts(comp,(0,-1,0),poly=True); R['5xF5_poly']=dict(ms=round(dt*1000,1), **c)
# ---- row 9: STEP ordering
def schema_of(path):
    txt=Path(path).read_text(errors='ignore'); i=txt.find('FILE_SCHEMA'); return txt[i:i+80].replace('\n',' ')
STEPControl_Controller.Init_s(); R['step_default']=Interface_Static.CVal_s('write.step.schema')
Interface_Static.SetCVal_s('write.step.schema','AP242DIS'); w=STEPControl_Writer(); w.Transfer(F1, STEPControl_AsIs); w.Write(str(OUT/'A.step')); R['step_A_set_before']=schema_of(OUT/'A.step')[:60]
Interface_Static.SetCVal_s('write.step.schema','AP214IS'); w=STEPControl_Writer(); w.Transfer(F1, STEPControl_AsIs); Interface_Static.SetCVal_s('write.step.schema','AP242DIS'); w.Write(str(OUT/'G.step')); R['step_G_set_after']=schema_of(OUT/'G.step')[:60]
w.Model(True); w.Transfer(F1, STEPControl_AsIs); w.Write(str(OUT/'H.step')); R['step_H_model_reset']=schema_of(OUT/'H.step')[:60]
# ---- row 10: F8 via XCAF with names, AP242, read back
def xcaf_doc():
    doc=TDocStd_Document(TCollection_ExtendedString("BinXCAF")); XCAFApp_Application.GetApplication_s().NewDocument(TCollection_ExtendedString("BinXCAF"), doc); return doc
doc=xcaf_doc(); st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
for k in range(10):
    tr=gp_Trsf(); tr.SetTranslation(gp_Vec(250*(k%5), 250*(k//5), 0)); s=BRepBuilderAPI_Transform(F5, tr, True).Shape()
    lab=st.AddShape(s, False); TDataStd_Name.Set_s(lab, TCollection_ExtendedString(f"plate_{k}"))
Interface_Static.SetCVal_s('write.step.schema','AP242DIS')
cw=STEPCAFControl_Writer(); cw.SetNameMode(True); cw.SetColorMode(True); t=time.time(); cw.Transfer(doc, STEPControl_AsIs); cw.Write(str(OUT/'F8.step')); R['F8_write_s']=round(time.time()-t,3); R['F8_schema']=schema_of(OUT/'F8.step')[:60]
t=time.time(); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(str(OUT/'F8.step')); doc2=xcaf_doc(); rd.Transfer(doc2); st2=XCAFDoc_DocumentTool.ShapeTool_s(doc2.Main())
labs=TDF_LabelSequence(); st2.GetFreeShapes(labs)
names=[]; total=0.0; faces=0
for i in range(1, labs.Length()+1):
    lab=labs.Value(i); s=st2.GetShape_s(lab); total+=vol(s); faces+=nunique(s,TopAbs_FACE)
    n=TDataStd_Name(); 
    if lab.FindAttribute(TDataStd_Name.GetID_s(), n): names.append(n.Get().ToExtString())
R['F8_read']=dict(s=round(time.time()-t,3), products=labs.Length(), faces=faces, vol=round(total,2), names=names[:3])
# ---- row 13: GLB variants of F1
import importlib
def glb(path, length_unit, zup):
    doc=xcaf_doc()
    if length_unit: XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)
    st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); BRepMesh_IncrementalMesh(F1, 0.1, False, 0.5, True); st.AddShape(F1, False)
    w=RWGltf_CafWriter(TCollection_AsciiString(str(path)), True); w.SetMergeFaces(True)
    if zup: w.ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
    w.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange())
    from tee.assets import gltf
    pr = gltf.probe(Path(path)); return pr.get('extents_m'), pr.get('dims_zup_m')
R['glb_unit_zup']=glb(OUT/'a.glb', True, True); R['glb_no_unit']=glb(OUT/'b.glb', False, True); R['glb_unit_only']=glb(OUT/'c.glb', True, False)
# ---- row 15: history on F1 fillet (4 vertical edges + seam)
mk=BRepFilletAPI_MakeFillet(F1); vert=[]
for e in edges_of(F1):
    c=BRepAdaptor_Curve(e)
    if c.GetType()==GeomAbs_Line:
        p1=c.Value(c.FirstParameter()); p2=c.Value(c.LastParameter())
        if abs(p1.X()-p2.X())<1e-9 and abs(p1.Y()-p2.Y())<1e-9: vert.append(e)
for e in vert: mk.Add(2.0, e)
mk.Build(); f1f=mk.Shape()
gen=[mk.Generated(e).Extent() for e in vert]
end_face=None; m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(F1, TopAbs_FACE, m)
mods=[]
for i in range(1,m.Extent()+1):
    f=TopoDS.Face_s(m.FindKey(i)); mods.append(mk.Modified(f).Extent())
R['history_fillet']=dict(vertical_edges=len(vert), generated_per_edge=gen, modified_per_face=mods, faces_after=nunique(f1f,TopAbs_FACE), vol=round(vol(f1f),3))
# ---- row 17: per-op wall times
def timed(fn):
    t=time.time(); r=fn(); return round((time.time()-t)*1000,1)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
def face_rect(w,h):
    pg=BRepBuilderAPI_MakePolygon(); 
    for x,y in [(0,0),(w,0),(w,h),(0,h)]: pg.Add(gp_Pnt(x,y,0))
    pg.Close(); return BRepBuilderAPI_MakeFace(pg.Wire()).Face()
R['ms_extrude']=timed(lambda: BRepPrimAPI_MakePrism(face_rect(100,60), gp_Vec(0,0,10)).Shape())
R['ms_hole1']=timed(lambda: BRepAlgoAPI_Cut(box(100,60,10), cyl(5,12,(50,30,-1))).Shape())
R['ms_hole100_nary']=timed(lambda: nary_cut(box(220,220,12), tools).Shape())
def fil8():
    mk=BRepFilletAPI_MakeFillet(F1)
    for e in edges_of(F1):
        c=BRepAdaptor_Curve(e); p1=c.Value(c.FirstParameter()); p2=c.Value(c.LastParameter())
        if c.GetType()==GeomAbs_Line and abs(p1.Z()-10)<1e-6 and abs(p2.Z()-10)<1e-6: mk.Add(2.0,e)
    return mk.Shape()
R['ms_fillet_top8']=timed(fil8)
def fil96():
    mk=BRepFilletAPI_MakeFillet(w3)
    for e in edges_of(w3): mk.Add(1.0,e)
    return mk.Shape()
R['ms_fillet_all_w3']=timed(fil96)
R['ms_fuse']=timed(lambda: unify(BRepAlgoAPI_Fuse(box(80,60,6), box(80,6,34,(0,0,6))).Shape()))
R['ms_hlr_F1']=R['F1_hlr_front']['ms']; R['ms_hlr_5xF5']=R['5xF5_exact']['ms']
R['ms_step_write_F5']=timed(lambda: (STEPControl_Writer().Transfer(F5, STEPControl_AsIs)))
def stepw():
    w=STEPControl_Writer(); w.Transfer(F5, STEPControl_AsIs); w.Write(str(OUT/'F5.step'))
R['ms_step_write_F5']=timed(stepw)
def stepr():
    r=STEPControl_Reader(); r.ReadFile(str(OUT/'F5.step')); r.TransferRoots(); return r.OneShape()
R['ms_step_read_F5']=timed(stepr)
R['ms_glb_F1']=timed(lambda: glb(OUT/'d.glb', True, True))
R['ms_mesh_F5']=timed(lambda: BRepMesh_IncrementalMesh(F5, 0.05, False, 0.5, True))
R['total_s']=round(time.time()-T0,2)
print(json.dumps(R, indent=1))
