
import os
import sys
import shutil
import arcpy
import numpy as np
import pandas as pd
import csv
import math
import time

pd.options.mode.chained_assignment = None  # default='warn'

# PATHS -------------------------------------------------------------------------------------------

sys_path = sys.argv[0]
abs_path = os.path.abspath(sys_path)
repo_path = os.path.dirname(os.path.dirname(abs_path))

# path to input folder
input_path = os.path.join(repo_path, "input")
input_mhn = os.path.join(input_path, "MHN_old.gdb")
# path to output folder
output_path = os.path.join(repo_path, "output")

# path to domain folder
domains = os.path.join(repo_path, "input", "mhn_domains")
# path to schema folder
schema = os.path.join(repo_path, "input", "mhn_schema")

def made_code_dict(name):
    code_dict = {}
    with open(os.path.join(domains, f"{name}.csv"), 'r') as csvfile:
        csvreader = csv.reader(csvfile)  # Reader object

        fields = next(csvreader)  # Read header
        for row in csvreader:     # Read rows
            code_dict[row[0]] = row[1]

    return code_dict

# MAKE GDB ----------------------------------------------------------------------------------------

if os.path.isdir(output_path) == True:
    shutil.rmtree(output_path)

os.mkdir(output_path)

# make output gdb
arcpy.management.CreateFileGDB(output_path, "MHN_new.gdb")
output_GDB = os.path.join(output_path, "MHN_new.gdb")
arcpy.env.workspace = output_GDB

arcpy.management.CreateFeatureDataset(output_GDB, "hwynet", 26771)

# ADD NODE DOMAINS --------------------------------------------------------------------------------

print("Adding node domains...")

name = "BINARY"
description = "0 or 1"
code_dict = pd.read_csv(os.path.join(domains, f"{name}.csv"), index_col = "Code")["Description"].to_dict()
arcpy.management.CreateDomain(output_GDB, name, description, "SHORT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

# add node domain
name = "NODE"
description = "Valid highway node IDs (<29999)"
arcpy.management.CreateDomain(output_GDB, name, description, "LONG", "RANGE", "DUPLICATE", "DEFAULT")
arcpy.management.SetValueForRangeDomain(output_GDB, name, 0, 29999)

# add subzone domain
name = "SUBZONE"
description = "CMAP trip generation zone (subzone) codes"
arcpy.management.CreateDomain(output_GDB, name, description, "LONG", "RANGE", "DEFAULT", "DEFAULT")
arcpy.management.SetValueForRangeDomain(output_GDB, name, 0, 17418)

# add zone domain
name = "ZONE"
description = "CMAP modeling zone (zone) codes"
arcpy.management.CreateDomain(output_GDB, name, description, "LONG", "RANGE", "DEFAULT", "DEFAULT")
arcpy.management.SetValueForRangeDomain(output_GDB, name, 1, 9999)

# add capzone domain
name = "CAPZONE"
description = "CMAP capacity zone (capzone) codes"
code_dict = pd.read_csv(os.path.join(domains, f"{name}.csv"), index_col = "Code")["Description"].to_dict()
arcpy.management.CreateDomain(output_GDB, name, description, "LONG", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

# ADD NODE FC -------------------------------------------------------------------------------------

print("Creating node feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "hwynet_node"
arcpy.management.CreateFeatureclass(workspace, name, "POINT")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

input_nodes = os.path.join(input_mhn, "hwynet", name)
fields = ["SHAPE@XY", "NODE", "POINT_X", "POINT_Y", "subzone17", "zone17", "capzone17", "IMAREA"]

with arcpy.da.SearchCursor(input_nodes, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:
            icursor.insertRow(row)

# ADD LINK DOMAINS --------------------------------------------------------------------------------

print("Adding link domains...")

name = "BASELINK"
description = "Skeleton or regular"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "DIRECTIONS"
description = "Link direction codes"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "VDF"
description = "Volume delay function (VDF) codes"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "AMPM"
description = "Time period restrictions"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "POSITIVE"
description = "Value must be >= 0"
arcpy.management.CreateDomain(output_GDB, name, description, "SHORT", "RANGE", "DUPLICATE", "DEFAULT")
arcpy.management.SetValueForRangeDomain(output_GDB, name, 0, 32767)

name = "PARKRES"
description = "Parking restrictions (string of affected time periods)"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "HWYMODE"
description = "Modes permitted on highway link"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "SRA"
description = "Strategic Regional Arterial (SRA) codes"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "TRUCKRTE"
description = "Truck route classification codes"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "BEARING"
description = "Simple bearing of link in from-to direction"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "VCLEARANCE"
description = "Overhead clearance (inches)"
arcpy.management.CreateDomain(output_GDB, name, description, "SHORT", "RANGE", "DUPLICATE", "DEFAULT")
arcpy.management.SetValueForRangeDomain(output_GDB, name, -1, 999)

# ADD LINK FC -------------------------------------------------------------------------------------

print("Creating link feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "hwynet_arc"
arcpy.management.CreateFeatureclass(workspace, name, "POLYLINE")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# prevent null here
for field in schema_list:

    field_name = field[0]

    if field_name not in ["SRA"]:
        arcpy.management.AlterField(name, field_name, field_is_nullable = "NON_NULLABLE")

input_links = os.path.join(input_mhn, "hwynet", name)
input_links_fields = [f.name for f in arcpy.ListFields(input_links) if (f.type!="Geometry" and f.name != "OBJECTID")]
input_links_df = pd.DataFrame(
            data = [row for row in arcpy.da.SearchCursor(input_links, input_links_fields)], 
            columns = input_links_fields)

link_dict = input_links_df.set_index("ABB").to_dict("index")

# save for later 
truckres_df = input_links_df[(input_links_df.MODES != "2") & (input_links_df.TRUCKRES != "0")][["ABB", "TRUCKRES"]]
truckres_dict = truckres_df.set_index("ABB")["TRUCKRES"].to_dict()
vclearance_df = input_links_df[(input_links_df.BASELINK == "0") & (input_links_df.VCLEARANCE != 0)][["ABB", "VCLEARANCE"]]
vclearance_dict = vclearance_df.set_index("ABB")["VCLEARANCE"].to_dict()

fields = ["SHAPE@", "ANODE", "BNODE", "BASELINK", "ABB",
          "ROADNAME", "DIRECTIONS", "TYPE1", "TYPE2", "AMPM1", "AMPM2",
          "POSTEDSPEED1", "POSTEDSPEED2", "THRULANES1", "THRULANES2",
          "THRULANEWIDTH1", "THRULANEWIDTH2", "PARKLANES1", "PARKLANES2",
          "SIGIC", "RRGRADECROSS", "VCLEARANCE", "NHSIC",
          "CHIBLVD", "TOLLSYS", "TRUCKRTE", "MESO", "MILES", "BEARING"]

with arcpy.da.SearchCursor(input_links, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:
            icursor.insertRow(row)

fields = ["ABB", "PARKRES1", "PARKRES2", "CLTL", "TOLLDOLLARS", "MODES", "SRA"]
with arcpy.da.UpdateCursor(name, fields) as ucursor:
    for row in ucursor:

        abb = row[0]

        if link_dict[abb]["PARKRES1"] in ["3", "7", "37"]:
            row[1] = link_dict[abb]["PARKRES1"]

        if link_dict[abb]["PARKRES2"] in ["3", "7", "37"]:
            row[2] = link_dict[abb]["PARKRES2"]

        if link_dict[abb]["CLTL"] in [0, 1]:
            row[3] = link_dict[abb]["CLTL"]
        elif link_dict[abb]["CLTL"] == 2:
            row[3] = 1

        if link_dict[abb]["TOLLDOLLARS"] != 0:

            toll = link_dict[abb]["TOLLDOLLARS"]
            toll_string = f'{toll:.6f}'.rstrip("0").rstrip(".")
            row[4] = toll_string

        else:
            row[4] = "0"

        if link_dict[abb]["MODES"] in ["1","3","4","5"]:
            row[5] = link_dict[abb]["MODES"] + "00"
        elif link_dict[abb]["MODES"] == "2":
            truckres = link_dict[abb]["TRUCKRES"]
            if truckres in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                row[5] = "20" + truckres
            else:
                row[5] = "2" + truckres

        if len(link_dict[abb]["SRA"]) >= 3:
            row[6] = link_dict[abb]["SRA"]

        ucursor.updateRow(row)

# ADD HWYPROJ FC ----------------------------------------------------------------------------------

print("Creating hwyproj feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "hwyproj"
arcpy.management.CreateFeatureclass(workspace, name, "POLYLINE")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

for field_name in ["TIPID", "COMPLETION_YEAR"]:

    arcpy.management.AlterField(name, field_name, field_is_nullable = "NON_NULLABLE")

input_proj = os.path.join(input_mhn, "hwynet", name)
fields = ["SHAPE@", "TIPID", "COMPLETION_YEAR", "MCP_ID", "RSP_ID", "RCP_ID", "NOTES"]

with arcpy.da.SearchCursor(input_proj, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:

            tipid = row[1]
            leading0 = "0" * (8- len(tipid))
            tipid8 = leading0 + tipid
            tipid10 = f"{tipid8[:2]}-{tipid8[2:4]}-{tipid8[4:]}"

            icursor.insertRow([row[0], tipid10, row[2], row[3], row[4], row[5], row[6]])

# ADD HWYPROJ CODING DOMAINS ----------------------------------------------------------------------

print("Adding hwyproj coding domains...")

name = "ACTION"
description = "Highway project action code"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "ADDBINARY"
description = "-1 or 0 or 1"
code_dict = pd.read_csv(os.path.join(domains, f"{name}.csv"), index_col = "Code")["Description"].to_dict()
arcpy.management.CreateDomain(output_GDB, name, description, "SHORT", "CODED", "DUPLICATE", "DEFAULT")
for code in code_dict:        
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

# ADD HWYPROJ CODING TABLE ------------------------------------------------------------------------

print("Creating hwyproj coding table...")

name = "hwyproj_coding"
arcpy.management.CreateTable(output_GDB, name)

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# prevent null here
for field in schema_list:

    field_name = field[0]
    arcpy.management.AlterField(name, field_name, field_is_nullable = "NON_NULLABLE")

input_coding = os.path.join(input_mhn, name)
s_fields = ["TIPID", "ABB", "ACTION_CODE", "NEW_DIRECTIONS", # 0-3
            "NEW_TYPE1", "NEW_TYPE2", "NEW_AMPM1", "NEW_AMPM2", # 4-7
            "NEW_POSTEDSPEED1", "NEW_POSTEDSPEED2", "NEW_THRULANES1", "NEW_THRULANES2", # 8-11
            "NEW_THRULANEWIDTH1", "NEW_THRULANEWIDTH2", "ADD_PARKLANES1", "ADD_PARKLANES2", # 12-15
            "ADD_SIGIC", "ADD_CLTL", "ADD_RRGRADECROSS", "NEW_TOLLDOLLARS", "NEW_MODES"] # 16-20

i_fields = ["TIPID", "ABB", "ACTION_CODE", "NEW_DIRECTIONS", # 0-3
            "NEW_TYPE1", "NEW_TYPE2", "NEW_AMPM1", "NEW_AMPM2", # 4-7
            "NEW_POSTEDSPEED1", "NEW_POSTEDSPEED2", "NEW_THRULANES1", "NEW_THRULANES2", # 8-11
            "NEW_THRULANEWIDTH1", "NEW_THRULANEWIDTH2", "ADD_PARKLANES1", "ADD_PARKLANES2", # 12-15
            "ADD_SIGIC", "ADD_CLTL", "ADD_RRGRADECROSS", "NEW_TOLLDOLLARS", "NEW_MODES"] # 16-20

with arcpy.da.SearchCursor(input_coding, s_fields, "ACTION_CODE <> '2'") as scursor:
    with arcpy.da.InsertCursor(name, i_fields) as icursor:

        for row in scursor:

            tipid = row[0]
            leading0 = "0" * (8- len(tipid))
            tipid8 = leading0 + tipid
            tipid10 = f"{tipid8[:2]}-{tipid8[2:4]}-{tipid8[4:]}"

            toll = row[19]
            toll_string = f'{toll:.6f}'.rstrip("0").rstrip(".")

            modes = row[20]
            new_modes = "0" if modes == "0" else modes + "00"

            insert_row = [
                tipid10,
                row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10],
                row[11], row[12], row[13], row[14], row[15],
                row[16], row[17], row[18], 
                toll_string,
                new_modes
            ]

            icursor.insertRow(insert_row)

# CHANGE MODES 
with arcpy.da.UpdateCursor(name, ["ABB", "NEW_MODES"], "ACTION_CODE = '4' AND NEW_MODES = '200'") as ucursor:
    for row in ucursor:
        
        if row[0] in truckres_dict:

            truckres = truckres_dict[row[0]]

            new_mode = f"20{truckres}" if len(truckres) == 1 else f"2{truckres}"
            row[1] = new_mode
            ucursor.updateRow(row)

# CHANGE VCLEARANCE
with arcpy.da.UpdateCursor(name, ["ABB", "NEW_VCLEARANCE"], "ACTION_CODE = '4'") as ucursor:
    for row in ucursor:
        
        if row[0] in vclearance_dict:

            vclearance = vclearance_dict[row[0]]
            
            row[1] = vclearance
            ucursor.updateRow(row)

new_links = os.path.join(output_GDB, "hwynet", "hwynet_arc")
new_links_fields = [f.name for f in arcpy.ListFields(new_links) if (f.type!="Geometry" and f.name != "OBJECTID")]
new_links_df = pd.DataFrame(
            data = [row for row in arcpy.da.SearchCursor(new_links, new_links_fields, "BASELINK = '1'")], 
            columns = new_links_fields)

link_dict = new_links_df.set_index(["ANODE", "BNODE"]).to_dict("index")

s_fields = ["TIPID", "ABB", "REP_ANODE", "REP_BNODE"]

i_fields = ["TIPID", "ABB", "ACTION_CODE", "NEW_DIRECTIONS", # 0-3
            "NEW_TYPE1", "NEW_TYPE2", "NEW_AMPM1", "NEW_AMPM2", # 4-7
            "NEW_POSTEDSPEED1", "NEW_POSTEDSPEED2", "NEW_THRULANES1", "NEW_THRULANES2", # 8-11
            "NEW_THRULANEWIDTH1", "NEW_THRULANEWIDTH2", "ADD_PARKLANES1", "ADD_PARKLANES2", # 12-15
            "ADD_SIGIC", "ADD_CLTL", "ADD_RRGRADECROSS", "NEW_TOLLDOLLARS", "NEW_MODES", # 16-20
            "NEW_VCLEARANCE"] # 21


rep_abbs = set()
rep_abb_dict = {}

with arcpy.da.SearchCursor(input_coding, s_fields, "ACTION_CODE = '2'") as scursor:
    with arcpy.da.InsertCursor(name, i_fields) as icursor:

        for row in scursor:

            tipid = row[0]
            leading0 = "0" * (8- len(tipid))
            tipid8 = leading0 + tipid
            tipid10 = f"{tipid8[:2]}-{tipid8[2:4]}-{tipid8[4:]}"

            abb = row[1]
            rep_anode = row[2]
            rep_bnode = row[3]

            if (rep_anode, rep_bnode) not in link_dict:
                # print(rep_anode, rep_bnode)
                continue
                
            attrs = link_dict[(rep_anode, rep_bnode)]

            new_directions = attrs["DIRECTIONS"]
            new_type1 = attrs["TYPE1"]
            new_type2 = attrs["TYPE2"]
            new_ampm1 = attrs["AMPM1"]
            new_ampm2 = attrs["AMPM2"]
            new_postedspeed1 = attrs["POSTEDSPEED1"]
            new_postedspeed2 = attrs["POSTEDSPEED2"]
            new_thrulanes1 = attrs["THRULANES1"]
            new_thrulanes2 = attrs["THRULANES2"]
            new_thrulanewidth1 = attrs["THRULANEWIDTH1"]
            new_thrulanewidth2 = attrs["THRULANEWIDTH2"]
            add_parklanes1 = attrs["PARKLANES1"]
            add_parklanes2 = attrs["PARKLANES2"]
            add_sigic = attrs["SIGIC"]
            add_cltl = attrs["CLTL"]
            add_rrgradecross = attrs["RRGRADECROSS"]
            new_tolldollars = attrs["TOLLDOLLARS"]
            new_modes = attrs["MODES"]
            new_vclearance = attrs["VCLEARANCE"]

            insert_row = [
                tipid10, abb, '4', new_directions, new_type1, new_type2,
                new_ampm1, new_ampm2, new_postedspeed1, new_postedspeed2, new_thrulanes1,
                new_thrulanes2, new_thrulanewidth1, new_thrulanewidth2, add_parklanes1, add_parklanes2,
                add_sigic, add_cltl, add_rrgradecross, 
                new_tolldollars, new_modes, new_vclearance
            ]

            rep_abb = f"{rep_anode}-{rep_bnode}-1"
            
            rep_abbs.add(rep_abb)

            if rep_abb not in rep_abb_dict:
                rep_abb_dict[rep_abb] = [abb]
            else:
                rep_abb_dict[rep_abb].append(abb)

            icursor.insertRow(insert_row)

print(f"{len(rep_abbs)} links were replaced. Check csv for attributes.")
rep_abbs_df = new_links_df[new_links_df.ABB.isin(rep_abbs)]

field_list = ["ABB", "PARKRES1", "PARKRES2", "NHSIC", "SRA", 
              "CHIBLVD", "TOLLSYS", "TRUCKRTE", "MESO", "REPLACES"]

def replace_abbs(abb):

    return ", ".join(rep_abb_dict[abb])

rep_abbs_df["REPLACES"] = rep_abbs_df["ABB"].apply(replace_abbs)

rep_abbs_df[field_list].to_csv(os.path.join(output_path, "replaced_abbs.csv"), index = False)

# ADD BUS DOMAINS ---------------------------------------------------------------------------------

print("Adding bus domains...")

name = "BUSMODE"
description = "Bus mode code"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "CTVEH"
description = "Activity-based model vehicle classes"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "CARDINAL"
description = "Cardinal directions"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "HOUR"
description = "Hours since midnight"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "SHORT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "DWELLCODE"
description = "Emme transit dwell code"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "TTF"
description = "Emme transit time function code"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

name = "IMPUTED"
description = "Flag to indicate that segment was imputed"
code_dict = made_code_dict(name)
arcpy.management.CreateDomain(output_GDB, name, description, "TEXT", "CODED", "DEFAULT", "DEFAULT")
for code in code_dict:
    arcpy.management.AddCodedValueToDomain(output_GDB, name, code, code_dict[code])

# ADD BUS BASE ------------------------------------------------------------------------------------

print("Creating bus base feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "bus_base"
arcpy.management.CreateFeatureclass(workspace, name, "POLYLINE")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

input_fc = os.path.join(input_mhn, "hwynet", name)
fields = ["SHAPE@", "TRANSIT_LINE", "DESCRIPTION", "MODE", "VEHICLE_TYPE", "HEADWAY", "SPEED",
          "ROUTE_ID", "LONGNAME", "DIRECTION", "TERMINAL", "START", "STARTHOUR", "AM_SHARE", "FEEDLINE"]

with arcpy.da.SearchCursor(input_fc, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:
            icursor.insertRow(row)

# ADD BUS CURRENT ---------------------------------------------------------------------------------

print("Creating bus current feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "bus_current"
arcpy.management.CreateFeatureclass(workspace, name, "POLYLINE")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# ADD BUS FUTURE ----------------------------------------------------------------------------------

print("Creating bus future feature class...")

workspace = os.path.join(output_GDB, "hwynet")
name = "bus_future"
arcpy.management.CreateFeatureclass(workspace, name, "POLYLINE")

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# ADD BUS BASE ITIN -------------------------------------------------------------------------------

print("Creating bus base itinerary table...")

name = "bus_base_itin"
arcpy.management.CreateTable(output_GDB, name)

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

input_table = os.path.join(input_mhn, name)
fields = ["TRANSIT_LINE", "ITIN_ORDER", "ITIN_A", "ITIN_B",
          "ABB", "LAYOVER", "DWELL_CODE", "ZONE_FARE",
          "LINE_SERV_TIME", "TTF", "LINK_STOPS", "IMPUTED", 
          "DEP_TIME", "ARR_TIME", "F_MEAS", "T_MEAS"]

start_time = time.time()

with arcpy.da.SearchCursor(input_table, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:
            
            ttf = row[9]

            if ttf == "0":
                ttf = "1"

            icursor.insertRow([
                row[0], row[1], row[2], row[3],
                row[4], row[5], row[6], row[7],
                row[8], ttf, row[10], row[11],
                row[12], row[13], row[14], row[15]
            ])

end_time = time.time()
total_time = round(end_time - start_time)
minutes = math.floor(total_time / 60)
seconds = total_time % 60

print(f"{minutes}m {seconds}s to loop.")

# ADD BUS CURRENT ITIN ----------------------------------------------------------------------------

print("Creating bus current itinerary table...")

name = "bus_current_itin"
arcpy.management.CreateTable(output_GDB, name)

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# ADD BUS FUTURE ITIN -----------------------------------------------------------------------------

print("Creating bus future itinerary table...")

name = "bus_future_itin"
arcpy.management.CreateTable(output_GDB, name)

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

arcpy.management.AddFields(name,
                           schema_list)

# ADD PARKNRIDE TABLE -----------------------------------------------------------------------------

print("Creating park n ride table...")

name = "parknride"
arcpy.management.CreateTable(output_GDB, name)

schema_df = pd.read_csv(os.path.join(schema, f"{name}.csv"))
schema_df = schema_df.replace(np.nan, None)

schema_list = [[row["NAME"], 
                row["TYPE"], 
                row["ALIAS"], 
                row["LENGTH"], 
                row["DEFAULT"], 
                row["DOMAIN"]] 
               for index, row in schema_df.iterrows()]

input_table = os.path.join(input_mhn, name)
arcpy.management.AddFields(name,
                           schema_list)

fields = ["FACILITY", "NODE", "COST", "SPACES", "ESTIMATE", "SCENARIO"]

with arcpy.da.SearchCursor(input_table, fields) as scursor:
    with arcpy.da.InsertCursor(name, fields) as icursor:

        for row in scursor:
            icursor.insertRow(row)

# ADD RELATIONSHIP CLASSES ------------------------------------------------------------------------

print("Adding relationship classes...")

# add rel_hwyproj_to_coding
arcpy.management.CreateRelationshipClass(
    "hwyproj", "hwyproj_coding", "rel_hwyproj_to_coding",
    "COMPOSITE", "hwyproj_coding", "hwyproj", "FORWARD", "ONE_TO_MANY", 
    "NONE", "TIPID", "TIPID")
        
# add rel_arcs_to_hwyproj_coding
arcpy.management.CreateRelationshipClass(
    "hwynet_arc", "hwyproj_coding", "rel_arcs_to_hwyproj_coding",
    "SIMPLE", "hwyproj_coding", "hwynet_arc", "NONE", "ONE_TO_MANY", 
    "NONE", "ABB", "ABB")
        
# add rel_bus_x_to_itin
xes = ["base", "current", "future"]

for x in xes:
    arcpy.management.CreateRelationshipClass(
        f"bus_{x}", f"bus_{x}_itin", f"rel_bus_{x}_to_itin",
        "COMPOSITE", f"bus_{x}_itin", f"bus_{x}", "FORWARD", "ONE_TO_MANY", 
        "NONE", "TRANSIT_LINE", "TRANSIT_LINE")
            
# add rel_arcs_to_bus_x_itin
for x in xes:
    arcpy.management.CreateRelationshipClass(
        "hwynet_arc", f"bus_{x}_itin", f"rel_arcs_to_bus_{x}_itin",
        "SIMPLE", f"bus_{x}_itin", "hwynet_arc", "NONE", "ONE_TO_MANY",
        "NONE", "ABB", "ABB")
            
# add rel_nodes_to_parknride
arcpy.management.CreateRelationshipClass(
    "hwynet_node", "parknride", "rel_nodes_to_parknride",
    "SIMPLE", "parknride", "hwynet_node", "NONE", "ONE_TO_MANY",
    "NONE", "NODE", "NODE")

print("Done")