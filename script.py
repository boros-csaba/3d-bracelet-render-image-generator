import bpy, math, csv, json, os.path, random
from mathutils import Matrix
from bpy_extras.object_utils import world_to_camera_view

rootPath = "C:/Users/boros/Desktop/elenora/3d-rendering/"
componentsRootPath = "C:/Users/boros/Desktop/elenora/elenora/wwwroot/images/components/"

products = []
createdComponents = []
createdMeshes = []
createdMaterials = []
createdImages = []
multipleAngles = False


def loadProductsFromFile(fileName):
	csvFile = open(rootPath + fileName, "r")
	csvReader = csv.reader(csvFile)
	for line in csvReader:
		braceletId = line[0]
		componentIds = []
		for index, componentId in enumerate(line):
			if index > 0:
				componentIds.append(componentId)
		products.append({ "id": braceletId, "componentIds": componentIds })
	csvFile.close()

jsonFile = open(rootPath + "components.json", "r")
components = json.load(jsonFile)
jsonFile.close()

def createNormalMap(newMaterial, componentData):
	nodes = newMaterial.node_tree.nodes
	principledBSDF = nodes.get("Principled BSDF")
	normalMap = nodes.new(type = "ShaderNodeNormalMap")
	normalMap.inputs[0].default_value = 1
	links = newMaterial.node_tree.links
	links.new(normalMap.outputs[0], principledBSDF.inputs[20])
	normalImage = nodes.new(type = "ShaderNodeTexImage")
	normalImage.image = bpy.data.images.load("C:/Users/boros/Desktop/elenora/3d-rendering/textures/normals/metal.jpg")
	createdImages.append(normalImage.image)
	normalImage.image.colorspace_settings.name = "Non-Color"
	textureMapping = nodes.get("ShaderNodeMapping")
	if textureMapping is not None:
		links.new(textureMapping.outputs[0], normalImage.inputs[0])
	links.new(normalImage.outputs[0], normalMap.inputs[1])
	
	
def createImageTexture(componentData, newMaterial):
	nodes = newMaterial.node_tree.nodes
	principledBSDF = nodes.get("Principled BSDF")
	if componentData["useImage"] == "False":
		principledBSDF.inputs[0].default_value = (componentData["color"][0], componentData["color"][1], componentData["color"][2], 1)
	else:
		imagePath = componentsRootPath + componentData["idString"] + "/3d/" + componentData["idString"] + "-1-1024.png"
		if "imageId" in componentData:
			imagePath = componentsRootPath + componentData["idString"] + "/3d/" + componentData["idString"] + "-" + str(componentData["imageId"]) + "-1024.png"
			if not os.path.isfile(imagePath):
				imagePath = componentsRootPath + componentData["idString"] + "/" + componentData["idString"] + "-" + str(componentData["imageId"]) + "-1024.png"
		if not os.path.isfile(imagePath):
			imagePath = componentsRootPath + componentData["idString"] + "/" + componentData["idString"] + "-1-1024.png"
		if not os.path.isfile(imagePath):
			imagePath = componentsRootPath + componentData["idString"] + ".png"
		imageTexture = nodes.new(type = "ShaderNodeTexImage")
		imageTexture.image = bpy.data.images.load(imagePath)
		createdImages.append(imageTexture.image)
		imageTexture.image.colorspace_settings.name = "sRGB"
		imageTexture.extension = "REPEAT"
		
		links = newMaterial.node_tree.links
		links.new(imageTexture.outputs[0], principledBSDF.inputs[0])
		textureMapping = nodes.new(type = "ShaderNodeMapping")
		textureMapping.name = "ShaderNodeMapping"
		textureMapping.inputs[1].default_value = (0, 0, 0)
		textureMapping.inputs[3].default_value = (2, 1, 1)
		
		links.new(textureMapping.outputs[0], imageTexture.inputs[0])
		textureCoordinates = nodes.new(type = "ShaderNodeTexCoord")
		textureCoordinates.name = "ShaderNodeTexCoord"
		links.new(textureCoordinates.outputs[2], textureMapping.inputs[0])
 
def getAllComponentsById(componentId):
	selectedComponents = []
	for index, component in enumerate(components):
		if component["id"] == componentId:
			selectedComponents.append(component)
	return selectedComponents

def getBeadCountInBracelet(componentId, bracelet):
	count = 0
	for index, id in enumerate(bracelet):
		if id == componentId:
			count = count + 1
	return count

def getComponentVariation(componentData, bracelet):
	if bracelet is None:
		return componentData
	variations = getAllComponentsById(componentData["id"])
	if componentData["FixedVariation"]:
		return componentData
	if len(variations) == 1:
		return componentData
	if getBeadCountInBracelet(componentData["id"], bracelet) == 1:
		return componentData
	return random.choices(variations, weights = map(lambda x: x["frequency"], variations))[0]

def cloneObject(newName, originalObjectName):
	meshTemplate = bpy.data.objects[originalObjectName]
	mesh = meshTemplate.data.copy()
	newObject = bpy.data.objects.new(newName, mesh)
	createdComponents.append(newObject)
	newObject.parent = bpy.data.objects["BraceletContainer"]
	createdMeshes.append(mesh)
	bpy.context.collection.objects.link(newObject)
	return newObject

def rotateSingleAxis(component, radians, axis): 
	component.rotation_euler = (component.rotation_euler.to_matrix() @ Matrix.Rotation(radians, 3, axis)).to_euler()
	

def rotateComponent(component, baseAngle):
	camera = bpy.data.objects["Camera"]
	deltaY = camera.location[1] - component.location[1]
	deltaX = camera.location[0] - component.location[0]
	deltaZ = camera.location[2] - component.location[2]
	rotationZ = math.atan2(deltaY, deltaX) + math.radians(baseAngle)
	rotationX = math.atan2(deltaZ, deltaY) + math.radians(180)
	rotateSingleAxis(component, rotationX, 'X')
	rotateSingleAxis(component, rotationZ, 'Z')
	rotateSingleAxis(component, math.radians(random.randint(0, 360)), 'Y')
	
def createComponent(name, componentData, location, angle, bracelet, sceneNr):
	newObject = None
	if componentData["type"] == "bead":
		componentData = getComponentVariation(componentData, bracelet)
		newObject = cloneObject(name, "Sphere")
		newObject.data.materials.clear()
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
		newObject.location = location
		newMaterial = bpy.data.materials.new(name = name)
		createdMaterials.append(newMaterial)
		newObject.data.materials.append(newMaterial)
		newMaterial.use_nodes = True
		nodes = newMaterial.node_tree.nodes
		principledBSDF = nodes.get("Principled BSDF")
		principledBSDF.inputs[7].default_value = componentData["roughness"]
		if "metalness" in componentData:
			principledBSDF.inputs[4].default_value = componentData["metalness"]
		createImageTexture(componentData, newMaterial)
		createNormalMap(newMaterial, componentData)
		newObject.active_material = newMaterial
		newObject.constraints.new("TRACK_TO")
		newObject.constraints["Track To"].target = bpy.data.objects["Empty"]
		newObject.constraints["Track To"].track_axis = "TRACK_Y"
		newObject.constraints["Track To"].up_axis = "UP_X"
	if componentData["type"] == "complex":
		componentData = getComponentVariation(componentData, bracelet)
		newObject = cloneObject(name, componentData["object"])
		newObject.location = location
		scale = 1
		if "scale" in componentData:
			scale = componentData["scale"]
		scaleX = scale
		if "scaleX" in componentData:
			scaleX = componentData["scaleX"]
		newObject.scale = (scaleX, scale, scale)
		rotationX = 0
		if "rotationX" in componentData:
			rotationX = componentData["rotationX"]
		rotationY = 0
		if "rotationY" in componentData:
			rotationY = componentData["rotationY"]
		rotationZ = -angle
		if "rotationZ" in componentData:
			rotationZ = rotationZ + componentData["rotationZ"]
		newObject.rotation_euler = (math.radians(rotationX), math.radians(rotationY), math.radians(rotationZ))
	if componentData["type"] == "rosequarz":
		newObject = cloneObject(name, "RoseQuarz")
		newObject.data.materials.clear()
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
		newObject.location = location
		newObject.active_material = bpy.data.materials.get("RoseQuarz")
	if componentData["type"] == "lava":
		newObject = cloneObject(name, "Lava")
		newObject.data.materials.clear()
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
		newObject.location = location
		newObject.active_material = bpy.data.materials.get("Lava")
		nodes = newObject.active_material.node_tree.nodes
		principledBSDF = nodes.get("Principled BSDF")
		principledBSDF.inputs[7].default_value = componentData["roughness"]
		principledBSDF.inputs[0].default_value = (componentData["color"][0], componentData["color"][1], componentData["color"][2], 1)
		rotateComponent(newObject, 90)
	if componentData["type"] == "knotCover":
		newObject = cloneObject(name, "KnotCoverMesh")
		newObject.location = location
		newObject.rotation_euler = (0, 0, math.radians(-angle + 90))
	if componentData["type"] == "disk":
		newObject = cloneObject(name, "Disk")
		newObject.location = location
		newObject.scale = (0.0008, 0.00125, 0.00125)
		newObject.rotation_euler = (0, 0, math.radians(-angle))
		newMaterial = bpy.data.materials.new(name = name)
		createdMaterials.append(newMaterial)
		newObject.data.materials.append(newMaterial)
		newMaterial.use_nodes = True
		nodes = newMaterial.node_tree.nodes
		principledBSDF = newObject.data.materials[0].node_tree.nodes.get("Principled BSDF")
		principledBSDF.inputs[0].default_value = (componentData["color"][0], componentData["color"][1], componentData["color"][2], 1)
		principledBSDF.inputs[4].default_value = 1
		principledBSDF.inputs[7].default_value = 0
	if componentData["type"] == "rondell":
		rings = cloneObject(name + "-ring", "RondellRing")
		rings.location = location
		rings.scale = (0.00022, 0.00027, 0.00027)
		rings.rotation_euler = (0, 0, math.radians(-angle))
		diamonds = cloneObject(name + "-diamond", "RondellDiamond")
		diamonds.location = location
		diamonds.scale = (0.00022, 0.00027, 0.00027)
		diamonds.rotation_euler = (0, 0, math.radians(-angle))
		principledBSDF = diamonds.data.materials[0].node_tree.nodes.get("Principled BSDF")
		principledBSDF.inputs[0].default_value = (componentData["color"][0], componentData["color"][1], componentData["color"][2], 1)
		newObject = diamonds
	if componentData["type"] == "heart":
		newObject = cloneObject(name, "Heart")
		newObject.location = location
		newObject.scale = (0.00085, 0.00085, 0.00085)
		newObject.rotation_euler = (0, 0, math.radians(-angle + 90))
		newMaterial = bpy.data.materials.new(name = name)
		createdMaterials.append(newMaterial)
		newObject.data.materials.append(newMaterial)
		newMaterial.use_nodes = True
		nodes = newMaterial.node_tree.nodes
		principledBSDF = newObject.data.materials[0].node_tree.nodes.get("Principled BSDF")
		principledBSDF.inputs[0].default_value = (componentData["color"][0], componentData["color"][1], componentData["color"][2], 1)
		principledBSDF.inputs[4].default_value = 1
		principledBSDF.inputs[7].default_value = 0
		camera = bpy.data.objects["Camera"]
		newObject.rotation_euler.y = camera.rotation_euler.x - 1.3
	if componentData["type"] == "hamsaHand":
		newObject = cloneObject(name, "HamsaHand")
		newObject.location = location
		newObject.scale = (0.001, 0.001, 0.0008)
		newObject.rotation_euler = (0, math.radians(75), math.radians(-angle + 90))
	if componentData["type"] == "redJasper":
		newObject = cloneObject(name, "RedJasper")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "dalmatianJasper":
		newObject = cloneObject(name, "DalmatianJasper")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "crackleQuartz":
		newObject = cloneObject(name, "CrackleQuartz")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "roseQuartz":
		newObject = cloneObject(name, "RoseQuarz")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "pinkJade":
		newObject = cloneObject(name, "PinkJade")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "metalLavaBlack":
		newObject = cloneObject(name, "MetalLavaBlack")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	if componentData["type"] == "greenAventurin":
		newObject = cloneObject(name, "GreenAventurin")
		newObject.location = location
		newObject.scale = (componentData["width"], componentData["width"], componentData["width"])
	
def getComponentById(componentId):
	componentIdParts = componentId.split("-")
	for index, component in enumerate(components):
		if str(component["id"]) == componentIdParts[0] and (len(componentIdParts) == 1 or str(component["imageId"]) == componentIdParts[1]):
			component["FixedVariation"] = len(componentIdParts) > 1
			return component
		
def getBraceletLength(braceletData):
	length = 0
	for index, componentId in enumerate(braceletData):
		component = getComponentById(componentId)
		if component is not None:
			length += component["width"]
		if componentId == "9999":
			return length
	return length

def getBraceletImageLocation(bracelet, sceneNr, outputFolder, angle):
	filename = "C:/Users/boros/Desktop/elenora/3d-rendering/" + outputFolder + "/" + bracelet["id"]
	if sceneNr > 0:
		filename = filename + "-" + str(sceneNr)
	if angle > -1:
		filename = filename + "-" + str(angle)
	filename = filename + ".jpg"
	return filename

def getBracelets(product):
	bracelets = []
	currentBracelet = []
	for index, componentId in enumerate(product["componentIds"]):
		if componentId == "9999":
			bracelets.append(currentBracelet)
			currentBracelet = []
		else:
			currentBracelet.append(componentId)
	bracelets.append(currentBracelet)
	return bracelets		

def createBracelet(bracelet, braceletNr, sceneNr):
	scale = 0.008
	length = getBraceletLength(bracelet)
	r = length / (2 * math.pi) * scale
	angle = 0
	prevComponentWidth = 0
	for index, componentId in enumerate(bracelet):
		component = getComponentById(componentId)
		if component is None:
			print("Missing component: " + str(componentId))
			return False
		if (not "canRotate" in component or component["canRotate"] != "True") and multipleAngles:
			print("Cannot rotate " + component["idString"])
			return False
		if index > 0:
			angle += 360 * (prevComponentWidth / 2 + component["width"] / 2) / length
		prevComponentWidth = component["width"]
		posX = math.sin(math.pi * angle / 180) * r
		posY = math.cos(math.pi * angle / 180) * r
		posZ = scale / 2
		if braceletNr > 0:
			posX = posX + scale * 0.01
			posY = posY - scale * 0.01
			posZ = posZ + scale * 0.97 * braceletNr
		position = (posX, posY, posZ)
		createComponent("Component " + str(index + 1), component, position, angle, bracelet, sceneNr)
	return True
	
def createProduct(product, sceneNr, outputFolder):
	bracelets = getBracelets(product)
	for index, bracelet in enumerate(bracelets):
		if not createBracelet(bracelet, index, sceneNr):
			return False
	return True
 
def deleteCreatedComponents():
	for index, item in enumerate(createdComponents):
		bpy.data.objects.remove(item, do_unlink = True)
	createdComponents.clear()
	for index, item in enumerate(createdMeshes):
		bpy.data.meshes.remove(item, do_unlink = True)
	createdMeshes.clear()
	for index, item in enumerate(createdMaterials):
		bpy.data.materials.remove(item, do_unlink = True)
	createdMaterials.clear()
	for index, item in enumerate(createdImages):
		bpy.data.images.remove(item, do_unlink = True)
	createdImages.clear()
	
def setupCamera(location, rotation):
	camera = bpy.data.objects["Camera"]
	camera.location = location
	camera.rotation_euler = rotation
	empty = bpy.data.objects["Empty"]
	empty.location = location
	
def hideAllSceneElements():
	bpy.data.objects["Plane"].location = (0, 0, -100)
	bpy.data.objects["TransparentPlane"].location = (0, 0, -100)
	bpy.data.objects["MarbleTable"].location = (0, 0, -100)
	bpy.data.objects["Flowers1"].location = (0, 0, -100)
	bpy.data.objects["Flowers2"].location = (0, 0, -100)
	
def resetSceneDefaults():
	bpy.context.scene.render.film_transparent = False
	bpy.data.objects["SunDirect"].data.energy = 0.5
	bpy.data.objects["SunBack"].data.energy = 3.5
	bpy.data.objects["SunBack2"].data.energy = 0.5
	bpy.context.scene.cycles.samples = 500
	global multipleAngles
	multipleAngles = False

def setResolution(width, height):
	bpy.context.scene.render.resolution_x = width
	bpy.context.scene.render.resolution_y = height
	
def setupScene(sceneNr, product):
	hideAllSceneElements()
	resetSceneDefaults()
	plane = bpy.data.objects["Plane"]
	plane.rotation_euler.x = 0
	if sceneNr == 0:
		setResolution(2048, 2048)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		setupCamera((-0.008579, -0.107019, 0.054053), (1.1154, 0.01, -0.0779))
		if "9999" in product["componentIds"]:
			bpy.data.objects["SunBack2"].data.energy = 0.2
		bpy.data.objects["SunDirect"].data.energy = 0.3
		bpy.data.objects["SunBack"].data.energy = 0.3
		plane.cycles.is_shadow_catcher = True
		plane.location = (0.000301, -0.000107, -0.000059)
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.09
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 150
	if sceneNr == 1:
		setResolution(2048, 2048)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		setupCamera((-0.038579, 0.012981, 0.094053), (0.413643, 0.05009095, -2.00713))
		if "9999" in product["componentIds"]:
			bpy.data.objects["SunBack2"].data.energy = 0.2
		bpy.data.objects["SunDirect"].data.energy = 0.3
		bpy.data.objects["SunBack"].data.energy = 0.3
		plane.cycles.is_shadow_catcher = True
		plane.location = (0.000301, -0.000107, -0.000059)
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.09
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 150
	if sceneNr == 2:
		setResolution(2048, 2048)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.5
		setupCamera((-0.000193, -0.093754, 0.07134), (0.9787, 0, -0.027925093))
		bpy.data.objects["SunDirect"].data.energy = 0.5
		bpy.data.objects["SunBack"].data.energy = 1.49
		bpy.data.objects["MarbleTable"].location = (0, 0, 0)
		bpy.data.objects["Flowers1"].location = (0.054141, 0.100466, -0.077709)
		bpy.data.objects["Flowers2"].location = (-0.092818, 0.09802, -0.126255)
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.09
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 50
	if sceneNr == 3:
		setResolution(512, 512)
		bpy.context.scene.cycles.samples = 250
		global multipleAngles
		multipleAngles = True
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		setupCamera((0, -0.09, 0.044053), (1.122247, 0, 0))
		if "9999" in product["componentIds"]:
			bpy.data.objects["SunBack2"].data.energy = 0.2
		bpy.data.objects["SunDirect"].data.energy = 0.3
		bpy.data.objects["SunBack"].data.energy = 0.3
		plane.cycles.is_shadow_catcher = True
		plane.location = (0.000301, -0.000107, -0.000059)
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.09
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 150
	if sceneNr == 101:
		setResolution(2048, 2048)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		setupCamera((-0.008579, -0.107019, 0.054053), (1.1154, 0.01, -0.0779))
		bpy.data.objects["SunDirect"].data.energy = 0.3
		bpy.data.objects["SunBack"].data.energy = 0.3
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.09
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 150
	if sceneNr == 102:
		setResolution(1080, 1920)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		setupCamera((0, -0.2, 0.095), (1.22, 0, 0))
		bpy.data.objects["SunDirect"].data.energy = 0.3
		bpy.data.objects["SunBack"].data.energy = 0.3
		plane.cycles.is_shadow_catcher = True
		plane.location = (0.000301, -0.000107, -0.000059)
		bpy.data.objects["Camera"].data.dof.use_dof = True
		bpy.data.objects["Camera"].data.dof.focus_distance = 0.178
		bpy.data.objects["Camera"].data.dof.aperture_fstop = 150
	if sceneNr == 103:
		setResolution(4096, 4096)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1
		bpy.data.objects["SunDirect"].data.energy = 0.2
		bpy.data.objects["SunBack"].data.energy = 0.2
		plane.cycles.is_shadow_catcher = True
		plane.location = (0.000301, -0.000107, -0.000059)
		setupCamera((0, 0, 0.09), (0, 0, 0))
		bpy.data.objects["Camera"].data.dof.use_dof = False
		bpy.context.scene.render.film_transparent = True
	if sceneNr == 104:
		setResolution(4096, 4096)
		bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.5
		setupCamera((-0.004601, -0.051047, 0.015034), (1.115399782, 0.010000003576, -0.07789997864))
		bpy.data.objects["SunDirect"].data.energy = 0.5
		bpy.data.objects["SunBack"].data.energy = 1.49
		bpy.data.objects["MarbleTable"].location = (0, 0, 0)
		bpy.data.objects["Flowers1"].location = (0.054141, 0.100466, -0.077709)
		bpy.data.objects["Flowers2"].location = (-0.092818, 0.09802, -0.126255)
		bpy.data.objects["Camera"].data.dof.use_dof = False

def start(braceletsFile, scenes, outputFolder):  
	loadProductsFromFile(braceletsFile)
	for index, product in enumerate(products):
		for sceneNr in scenes:
			braceletFile = getBraceletImageLocation(product, sceneNr, outputFolder, -1)
			if not os.path.isfile(braceletFile):
				print("Creating bracelet: " + product["id"])	
				setupScene(sceneNr, product)
				if createProduct(product, sceneNr, outputFolder):
					bpy.context.scene.render.image_settings.file_format = "JPEG"
					global multipleAngles
					if multipleAngles == True:
						imageNr = 0
						for angle in range(0, 360, 2):
							braceletFile = getBraceletImageLocation(product, sceneNr, outputFolder + "/" + product["id"], imageNr)
							imageNr = imageNr + 1
							if not os.path.isfile(braceletFile):
								bpy.context.scene.render.filepath = braceletFile
								bpy.data.objects["BraceletContainer"].rotation_euler.z = math.radians(angle)
								bpy.ops.render.render(use_viewport = True, write_still = True)
								#return
						multipleAngles = False
					else:
						bpy.context.scene.render.filepath = braceletFile
						if sceneNr == 101:
							bpy.context.scene.render.image_settings.file_format = "PNG"
							bpy.context.scene.render.image_settings.color_mode = "RGBA"
						bpy.ops.render.render(use_viewport = True, write_still = True)
					#return
				deleteCreatedComponents()
	
print("done")
		
bpy.context.view_layer.update()