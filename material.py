import bpy

def create_bsdf_material(material, texture_set):
	nodes = material.node_tree.nodes

	location = (0, 0)
	incr = 200

	shader = nodes.get("Principled BSDF")
	shader.location = location

	location = (location[0], location[1] - incr)
	
	bpy.types.nodes.nw_add_multiple_images(filepath="Z:\\01_Work\\01_pro\\2019\\Lineup\\Assets\\MAD_CHR_Cube_001_M\\MAD_CHR_Cube_001_M_LODM\\MAD_CHR_Cube_001_M_T001_Face1_roughness.png", directory="Z:\\01_Work\\01_pro\\2019\\Lineup\\Assets\\MAD_CHR_Cube_001_M\\MAD_CHR_Cube_001_M_LODM\\", files=[{"name":"MAD_CHR_Cube_001_M_T001_Face1_basecolor.png", "name":"MAD_CHR_Cube_001_M_T001_Face1_basecolor.png"}, {"name":"MAD_CHR_Cube_001_M_T001_Face1_metallic.png", "name":"MAD_CHR_Cube_001_M_T001_Face1_metallic.png"}, {"name":"MAD_CHR_Cube_001_M_T001_Face1_normal.png", "name":"MAD_CHR_Cube_001_M_T001_Face1_normal.png"}, {"name":"MAD_CHR_Cube_001_M_T001_Face1_roughness.png", "name":"MAD_CHR_Cube_001_M_T001_Face1_roughness.png"}])

	return shader