import arcpy
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Create Order-2 Voronoi Diagram"
        self.alias = "CreateOrder2VoronoiDiagram"

        # List of tool classes associated with this toolbox
        self.tools = [CreateOrder2VoronoiDiagram]


class CreateOrder2VoronoiDiagram(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CreateOrder2VoronoiDiagram"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):
        in_features= arcpy.Parameter(
            displayName="Input Feature",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        out_features= arcpy.Parameter(
            displayName="Out Feature",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")
        params=[in_features, out_features] 
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_features=parameters[0].valueAsText
        out_features=parameters[1].valueAsText
        
        output                     = os.path.dirname(out_features)
        arcpy.env.scratchWorkspace = os.path.dirname(out_features)
        arcpy.env.workspace= output
        
        outlayerP = "Point_Layer"
        outlayerP_unselected = "Point_Layer_unselected"
        outlayerT = "Thiessen_Layer"
        outlayerT_unselected = "Thiessen_Layer_unselected"
        field="Input_FID"
        new_name_i="Input_FID_i"
        new_name_j="Input_FID_j"
        int_merge="merge"
        int_merge_c="merge_copy"
        layer_merge="layer_merge"
        merge="dyads"
        merge2="dyads_output"
                
        Path_thiessen= os.path.join(output, "thiessen")
        Path_thiessen2= os.path.join(output, "thiessen2")
        Path_thiessen_j= os.path.join(output, "thiessen_j")
        Path_int_merge=os.path.join(output, int_merge)
        Path_int_merge_copy=os.path.join(output, int_merge_c)
        Path_merge=os.path.join(output, merge)
        Path_merge2=os.path.join(output, merge2)

        Input_FID_i=[]
        Input_FID_j=[]

        
        arcpy.CreateThiessenPolygons_analysis(in_features, Path_thiessen)
        arcpy.AlterField_management(Path_thiessen, field, new_name_i)
        arcpy.MakeFeatureLayer_management(Path_thiessen, outlayerT)
        i=[]
        list = []
        with arcpy.da.SearchCursor(in_features, ("OBJECTID")) as cursor1:
            for row1 in cursor1:
                arcpy.MakeFeatureLayer_management (in_features, outlayerP) #put outside loop?
                arcpy.SelectLayerByAttribute_management(outlayerP,"NEW_SELECTION",'"OBJECTID" = {0}'.format(row1[0]))
                i="{0}".format(row1[0])
                arcpy.SelectLayerByLocation_management(outlayerT,"INTERSECT",outlayerP)
                t="t"
                Path_thiessen_copy= os.path.join(output, t)
                arcpy.CopyFeatures_management(outlayerT, Path_thiessen_copy)
                arcpy.SelectLayerByAttribute_management(outlayerP,"SWITCH_SELECTION",'"OBJECTID" = {0}'.format(row1[0]))
                arcpy.env.extent =Path_thiessen
                arcpy.CreateThiessenPolygons_analysis(outlayerP, Path_thiessen_j)
                arcpy.AlterField_management(Path_thiessen_j, field, new_name_j)
                t2="t2"
                t3="t3"
                arcpy.MakeFeatureLayer_management(Path_thiessen_j, t2)
                arcpy.MakeFeatureLayer_management(Path_thiessen_copy, t3)
                int_i = "int_"  + str(i)
                Path_Int=os.path.join(output, int_i)
                arcpy.Intersect_analysis([t3,t2],Path_Int)
                list.append(Path_Int)
        arcpy.Merge_management(list, Path_int_merge)   

        arcpy.CopyFeatures_management(Path_int_merge,Path_int_merge_copy)
        
        list2=[]
        arcpy.MakeFeatureLayer_management(Path_int_merge_copy, layer_merge)
        with arcpy.da.SearchCursor(Path_int_merge,("OBJECTID")) as cursor0:
            for row0 in cursor0:
                arcpy.SelectLayerByAttribute_management(layer_merge,"NEW_SELECTION",'"OBJECTID" = {0}'.format(row0[0]))
                result = arcpy.GetCount_management(layer_merge)
                count = int(result.getOutput(0))
                if count==1:
                    SC = arcpy.SearchCursor(layer_merge)
                    for row in SC:
                        I_FID_i = row.getValue(new_name_i)
                        I_FID_j = row.getValue(new_name_j)
                    dyad_merge="dyad_"  + str(I_FID_i) + "_" + str(I_FID_j)
                    Path_dyad_merge=os.path.join(output, dyad_merge)
                    dyad_merge2="d_"  + str(I_FID_i) + "_" + str(I_FID_j)
                    Path_dyad_merge2=os.path.join(output, dyad_merge2)
                    merge="dyads"
                    arcpy.SelectLayerByAttribute_management(layer_merge,"ADD_TO_SELECTION",'\"Input_FID_i\" = %d AND \"Input_FID_j\" = %d' %(I_FID_j,I_FID_i))  #works
                    arcpy.CopyFeatures_management(layer_merge, Path_dyad_merge)
                    arcpy.Dissolve_management(Path_dyad_merge,Path_dyad_merge2,"FID_t",statistics_fields=([new_name_i,"FIRST"],[new_name_j,"FIRST"]))
                    arcpy.DeleteFeatures_management(layer_merge)
                    list2.append(Path_dyad_merge2)
        arcpy.Merge_management(list2, out_features)                     
        return
