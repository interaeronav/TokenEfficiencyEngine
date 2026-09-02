#!/bin/zsh
set -u
SP=/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/ae03fe49-30f7-499f-8422-a328b5396550/scratchpad/p0a
cd $SP
cat > coverage.py <<'PY'
import time, resource, sys, importlib
t=time.time(); import OCP; imp=time.time()-t
mods = "BRepTools.BRepTools_History TNaming.TNaming_Builder HLRBRep.HLRBRep_Algo HLRBRep.HLRBRep_PolyAlgo HLRBRep.HLRBRep_HLRToShape RWGltf.RWGltf_CafWriter BRepFeat.BRepFeat_MakeDPrism XCAFDoc.XCAFDoc_DocumentTool BRepFilletAPI.BRepFilletAPI_MakeFillet BRepFilletAPI.BRepFilletAPI_MakeChamfer BRepOffsetAPI.BRepOffsetAPI_DraftAngle BRepOffsetAPI.BRepOffsetAPI_MakePipeShell BRepOffsetAPI.BRepOffsetAPI_ThruSections BRepOffsetAPI.BRepOffsetAPI_MakeThickSolid BRepAlgoAPI.BRepAlgoAPI_Splitter STEPCAFControl.STEPCAFControl_Writer STEPCAFControl.STEPCAFControl_Reader IntCurvesFace.IntCurvesFace_ShapeIntersector BRepClass3d.BRepClass3d_SolidClassifier GeomConvert.GeomConvert_BSplineCurveToBezierCurve ShapeUpgrade.ShapeUpgrade_UnifySameDomain OSD.OSD_Timer Message.Message_ProgressRange BRepExtrema.BRepExtrema_DistShapeShape BRepBndLib.BRepBndLib IGESControl.IGESControl_Writer StlAPI.StlAPI_Writer LocOpe.LocOpe_DPrism RWMesh.RWMesh_CoordinateSystem BRepMesh.BRepMesh_IncrementalMesh STEPControl.STEPControl_Writer Interface.Interface_Static TopExp.TopExp BRep.BRep_Tool GProp.GProp_GProps BRepGProp.BRepGProp".split()
missing=[]
for m in mods:
    mod, cls = m.rsplit('.',1)
    try:
        getattr(importlib.import_module('OCP.'+mod), cls)
    except Exception as e:
        missing.append(m)
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6
print(f"import_s={imp:.2f} bound={len(mods)-len(missing)}/{len(mods)} missing={missing} rss_mb={rss:.0f} vtk_in_sys_modules={'vtkmodules' in sys.modules}")
PY
for W in novtk vtk; do
  PKG=cadquery-ocp-novtk; [ $W = vtk ] && PKG=cadquery-ocp
  echo "=== $W ($PKG)"
  rm -rf venv_$W
  uv venv --python 3.11 venv_$W -q 2>&1 | tail -1
  /usr/bin/time -p uv pip install --python venv_$W/bin/python -q "$PKG==7.9.3.1.1" 2>&1 | tail -3
  SITE=$(venv_$W/bin/python -c "import sysconfig;print(sysconfig.get_paths()['purelib'])")
  echo "site: $SITE"; du -sh $SITE | tail -1; du -sh $SITE/OCP 2>/dev/null | tail -1
  SO=$(ls $SITE/OCP/OCP*.so | head -1); echo "so: $(du -h $SO | cut -f1) vtk_links=$(otool -L $SO | grep -c -i vtk)"
  echo "wheel OCP/ entries: $(grep -c '^OCP/' $SITE/${PKG//-/_}-7.9.3.1.1.dist-info/RECORD 2>/dev/null || ls $SITE/*.dist-info | head -3)"
  for i in 1 2 3 4; do echo -n "run$i: "; PYTHONDONTWRITEBYTECODE=1 venv_$W/bin/python coverage.py; done
done
echo "=== done"
