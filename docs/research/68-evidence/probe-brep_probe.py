import time, os, hashlib, sys
t0=time.time(); import OCP
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepTools import BRepTools
from OCP.TopTools import TopTools_FormatVersion
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from OCP.BRep import BRep_Tool, BRep_Builder
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line
imp=time.time()-t0
# a ~100-feature part: plate with 10x10 holes, then fillet the vertical hole edges? keep: 100 holes
t=time.time()
shape = BRepPrimAPI_MakeBox(220.0, 220.0, 12.0).Shape()
for i in range(10):
    for j in range(10):
        cyl = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(20+20*i, 20+20*j, -1), gp_Dir(0,0,1)), 4.0, 14.0).Shape()
        shape = BRepAlgoAPI_Cut(shape, cyl).Shape()
build=time.time()-t
def count(s, kind):
    n=0; ex=TopExp_Explorer(s, kind)
    while ex.More(): n+=1; ex.Next()
    return n
props=GProp_GProps(); BRepGProp.VolumeProperties_s(shape, props)
# B-rep fingerprint without triangulation: sorted face (type, area, centroid) tuples rounded
from OCP.BRepGProp import BRepGProp as G
faces=[]
ex=TopExp_Explorer(shape, TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); p=GProp_GProps(); G.SurfaceProperties_s(f,p); c=p.CentreOfMass()
    faces.append((round(p.Mass(),4), round(c.X(),4), round(c.Y(),4), round(c.Z(),4)))
    ex.Next()
faces.sort()
fp=hashlib.sha256(repr(faces).encode()).hexdigest()[:16]
t=time.time(); BRepTools.Write_s(shape, "cp_notri.brep", False, False, TopTools_FormatVersion.TopTools_FormatVersion_VERSION_3); w1=time.time()-t
t=time.time(); BRepTools.Write_s(shape, "cp_default.brep"); w2=time.time()-t
t=time.time(); back=TopoDS_Shape(); BRepTools.Read_s(back, "cp_notri.brep", BRep_Builder()); r1=time.time()-t
p2=GProp_GProps(); BRepGProp.VolumeProperties_s(back,p2)
print(f"import={imp:.2f}s build100holes={build:.3f}s faces={count(shape,TopAbs_FACE)} edges={count(shape,TopAbs_EDGE)} vol={props.Mass():.3f} fp={fp} write_notri={w1*1000:.1f}ms/{os.path.getsize('cp_notri.brep')}B write_default={w2*1000:.1f}ms/{os.path.getsize('cp_default.brep')}B read={r1*1000:.1f}ms vol_back={p2.Mass():.3f}")
# glTF with XCAFDoc_LengthUnit set to mm (0.001 m)
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.XCAFApp import XCAFApp_Application
from OCP.RWGltf import RWGltf_CafWriter
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.BRepMesh import BRepMesh_IncrementalMesh
doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF")); XCAFApp_Application.GetApplication_s().NewDocument(TCollection_ExtendedString("BinXCAF"), doc)
XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); BRepMesh_IncrementalMesh(shape, 0.1, False, 0.5, True); st.AddShape(shape, False)
w = RWGltf_CafWriter(TCollection_AsciiString("plate_mm.glb"), True); w.SetMergeFaces(True)
ok = w.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange())
import trimesh; g=trimesh.load("plate_mm.glb"); ext = g.extents if hasattr(g,'extents') else None
print(f"glb ok={ok} bytes={os.path.getsize('plate_mm.glb')} geoms={len(g.geometry)} extents={[round(float(v),4) for v in g.extents]} (expect ~[0.22,0.22,0.012] m)")
