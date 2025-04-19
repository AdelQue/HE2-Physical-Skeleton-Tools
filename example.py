from PBA import *

# Making custom PBA
main_name = "MainPBASkel"
bone_names = [f"regbone_{i+1}" for i in range(12)]

pba = PBA("NewPBASkeleton")

rigidbodies = [PBARigidBody(n) for n in bone_names]
pba.add_rigidbody(*rigidbodies)
    
constraints = [PBAConstraint(n) for n in bone_names[1:]]
pba.add_constraint(*constraints)

softbodies = [PBASoftBody(StringSegment("Softbody_Name_1")), PBASoftBody("Softbody_Name_2"), PBASoftBody("Softbody_Name_3"), PBASoftBody("Softbody_Name_4")]
pba.add_softbody(*softbodies)

for i, softbody in enumerate(pba.softbodies):
    keys = "ABCD"
    key = keys[i]
    soft_bone_names = [f"softbone{key}_{j+1}" for j in range(40)]
    nodes = [PBAClothNode(name) for name in soft_bone_names]
    softbody.add_nodes(*nodes)
    
    links = [PBAClothLink((j, j+1), 1.0) for j in range(86)]
    softbody.add_links(*links)

pba.structure_elements()
pba.export_file("output/custom_file.pba")


# Import/Export Existing PBA
filenames = [
    "bos_metaloverload",
    "chr_big",
    "chr_big_frontiers",
    "chr_knucklesdrill",
    "chr_kodama01",
    "chr_sage",
    "chr_shadow",
    "chr_shadow_dameba",
    "chr_shadow_dwing",
    "chr_terios",
    "enm_wolf01",
    "mbo_tracker01"
]

for filename in filenames:
    name_in = 'original/' + filename + '.pba'
    name_out = 'output/' + filename + '_out.pba'
    
    tmp_pba = PBA("temp")
    tmp_pba.import_file(name_in)
    tmp_pba.export_file(name_out)

    with open(name_in, 'rb') as file1:
        with open(name_out, 'rb') as file2:
            print(f"Same = {bool(file1.read()==file2.read())}\t{filename}")