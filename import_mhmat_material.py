#+
# This Blender addon imports a .mhmat material definition from
# MakeHuman into the current .blend file.
#
# Copyright 2020 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import sys
import os
import enum
import bpy
import bpy.props
import bpy_extras.io_utils

bl_info = \
    {
        "name" : "Import MakeHuman Material",
        "author" : "Lawrence D'Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 2, 4),
        "blender" : (2, 93, 0),
        "location" : "File > Import",
        "description" : "imports a material definition from a .mhmat file.",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Import-Export",
    }

#+
# Useful stuff
#-

class Failure(Exception) :

    def __init__(self, msg) :
        self.msg = msg
    #end __init__

#end Failure

def deselect_all(material_tree) :
    for node in material_tree.nodes :
        node.select = False
    #end for
#end deselect_all

#+
# Do the work
#-

@enum.unique
class MAP(enum.Enum) :
    # each value is a 3-tuple:
    # («name of input on Principled BSDF», «name of texture map attribute», «name of intensity attribute»)
    ALPHA = ("Alpha", "transparencymapTexture", "transparencymapIntensity")
    BUMP = ("Normal", "bumpmapTexture", "bumpmapIntensity")
    DIFFUSE = ("Base Color", "diffuseTexture", None)
    DISPLACEMENT = ("Displacement", "displacementmapTexture", "displacementmapIntensity")
    NORMAL = ("Normal", "normalmapTexture", "normalmapIntensity")
    SPECULAR = ("Specular", "specularmapTexture", "specularmapIntensity")

    @property
    def principled_bsdf_input_name(self) :
      # names of principled shader inputs are ['Base Color', 'Subsurface', 'Subsurface Radius',
      # 'Subsurface Color', 'Metallic', 'Specular', 'Specular Tint', 'Roughness',
      # 'Anisotropic', 'Anisotropic Rotation', 'Sheen', 'Sheen Tint', 'Clearcoat',
      # 'Clearcoat Roughness', 'IOR', 'Transmission', 'Transmission Roughness',
      # 'Emission', 'Alpha', 'Normal', 'Clearcoat Normal', 'Tangent']
        return \
            self.value[0]
    #end principled_bsdf_input_name

    @property
    def map_name(self) :
        return \
            self.value[1]
    #end map_name

    @property
    def intensity_name(self) :
        return \
            self.value[2]
    #end intensity_name

#end MAP

class ImportMakeHumanMaterial(bpy.types.Operator, bpy_extras.io_utils.ImportHelper) :
    bl_idname = "material.import_mhmat"
    bl_label = "Import MakeHuman Material"

    filter_glob : bpy.props.StringProperty \
      (
        default = "*.mhmat",
        options = {"HIDDEN"}
      )

    def execute(self, context) :

        convert_float = lambda words : float(words[0])

        def convert_colour(words) :
            return \
                tuple(float(c) for c in words) + (1,)
        #end convert_colour

        def def_convert_float_upto(maxval) :

            def convert(s) :
                val = float(s[0])
                if val < 0 or val > maxval :
                    raise ValueError("out of range")
                #end if
                return \
                    val
            #end convert

        #begin def_convert_float_upto
            return \
                convert
        #end def_convert_float_upto

        def def_load_image(is_colour) :

            def load_image(words) :
                pathname = os.path.join(os.path.dirname(self.filepath), " ".join(words))
                image = bpy.data.images.load(pathname)
                if not is_colour :
                    image.colorspace_settings.name = "Linear"
                #end if
                image.pack()
                image.name = os.path.split(pathname)[1]
                # wipe all traces of original source file path
                image.filepath = "//textures/%s" % os.path.split(pathname)[1]
                image.filepath_raw = image.filepath
                for item in image.packed_files :
                    item.filepath = image.filepath
                #end for
                return \
                    image
            #end load_image

        #begin def_load_image
            return \
                load_image
        #end def_load_image

        valid_keywords = \
            {
                "diffuseColor" :
                    {
                        "convert" : convert_colour,
                        "nr_args" : 3,
                        "default" : (1, 1, 1, 1),
                    },
                # "specularColor" not implemented
                "shininess" :
                    {
                        "convert" : def_convert_float_upto(1),
                        "nr_args" : 1,
                        "default" : 0,
                    },
                "emissiveColor" :
                    {
                        "convert" : convert_colour,
                        "nr_args" : 3,
                        "default" : (0, 0, 0, 1),
                    },
                "opacity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "diffuseTexture" :
                    {
                        "convert" : def_load_image(True),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "bumpmapTexture" :
                    {
                        "convert" : def_load_image(False),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "bumpmapIntensity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "normalmapTexture" :
                    {
                        "convert" : def_load_image(False),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "normalmapIntensity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "displacementmapTexture" :
                    {
                        "convert" : def_load_image(False),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "displacementmapIntensity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "specularmapTexture" :
                    {
                        "convert" : def_load_image(True),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "specularmapIntensity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "transparencymapTexture" :
                    {
                        "convert" : def_load_image(False),
                        "nr_args" : 1,
                        "default" : None,
                    },
                "transparencymapIntensity" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "sssEnabled" :
                    {
                        "convert" : bool,
                        "nr_args" : 1,
                        "default" : False,
                    },
                "sssRScale" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "sssGScale" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
                "sssBScale" :
                    {
                        "convert" : convert_float,
                        "nr_args" : 1,
                        "default" : 1,
                    },
            }

        ignored_keywords = \
            { # to be ignored quietly
                "alphaToCoverage", "castShadows", "description", "name", "receiveShadows",
                "shader", "shaderConfig", "tag", "transparent", "viewPortColor",
                "viewPortAlpha",
            }

        class Settings :
            __slots__ = ("name",) + tuple(valid_keywords.keys())
        #end Settings

    #begin execute
        try :
            settings = Settings()
            for keyword, entry in valid_keywords.items() :
                setattr(settings, keyword, entry["default"])
            #end for
            settings.name = os.path.basename(self.filepath)
              # don’t use name field from .mhmat file
            linenr = 0
            errors = []
            for line in open(self.filepath, "rt", encoding = "utf8") :
                linenr += 1
                line = line.strip()
                if not (line == "" or line.startswith("#") or line.startswith("//")) :
                    items = list(i for i in line.split() if i != "")
                    keyword = items[0]
                    rest = items[1:]
                    if keyword in valid_keywords :
                        try :
                            entry = valid_keywords[keyword]
                            if len(rest) != entry["nr_args"] :
                                raise ValueError("wrong nr args")
                            #end if
                            setattr(settings, keyword, entry["convert"](rest))
                        except ValueError as err :
                            raise Failure \
                              (
                                    "import_mhmat error: file %s, line %d: bad value for keyword %s"
                                %
                                    (self.filepath, linenr, repr(keyword))
                              )
                        #end try
                    elif keyword not in ignored_keywords :
                        sys.stderr.write \
                          (
                                "import_mhmat warning: file %s, line %d: unrecognized keyword %s\n"
                            %
                                (self.filepath, linenr, repr(keyword))
                          )
                    #end if
                #end if
            #end for
            material = bpy.data.materials.new(settings.name)
            material.use_nodes = True
            material.diffuse_color = settings.diffuseColor
            material_tree = material.node_tree
            for node in material_tree.nodes :
              # clear out default nodes
                material_tree.nodes.remove(node)
            #end for
            tex_coords = material_tree.nodes.new("ShaderNodeTexCoord")
            tex_coords.location = (-600, 0)
            tex_mapping = material_tree.nodes.new("ShaderNodeMapping")
            tex_mapping.location = (-400, 0)
            material_tree.links.new(tex_coords.outputs["UV"], tex_mapping.inputs["Vector"])
            fanout = material_tree.nodes.new("NodeReroute")
            fanout.location = (-200, -150)
            material_tree.links.new(tex_mapping.outputs["Vector"], fanout.inputs[0])
              # fanout makes it easy to change this coordinate source for all
              # texture components at once
            main_shader = material_tree.nodes.new("ShaderNodeBsdfPrincipled")
            main_shader.location = (500, 0)
            material_output = material_tree.nodes.new("ShaderNodeOutputMaterial")
            material_output.location = (850, 0)
            material_tree.links.new(main_shader.outputs[0], material_output.inputs[0])
            for attr, input in \
                (
                    ("diffuseColor", "Base Color"),
                    ("emissiveColor", "Emission"),
                    ("opacity", "Alpha"),
                ) \
            :
                main_shader.inputs[input].default_value = getattr(settings, attr)
            #end for
            main_shader.inputs["Subsurface"].default_value = (0, 1)[settings.sssEnabled]
            main_shader.inputs["Subsurface Radius"].default_value = \
                tuple(getattr(settings, "sss%sScale" % c) for c in ("R", "G", "B"))
            main_shader.inputs["Roughness"].default_value = 1.0 - settings.shininess
            map_location = [-100, 0]

            def new_image_texture_node(map) :
                tex_image = material_tree.nodes.new("ShaderNodeTexImage")
                tex_image.image = getattr(settings, map.map_name)
                tex_image.location = tuple(map_location)
                material_tree.links.new(tex_image.inputs[0], fanout.outputs[0])
                map_location[1] -= 300
                return \
                    tex_image
            #end new_image_texture_node

            def add_intensity_nodes(map, input_terminal, extra_nodes_location) :
                output_terminal = input_terminal
                if map.intensity_name != None :
                    intensity = getattr(settings, map.intensity_name)
                    if intensity != 1 :
                        intensify = material_tree.nodes.new("ShaderNodeMath")
                        intensify.location = extra_nodes_location
                        intensify.operation = "MULTIPLY"
                        intensify.inputs[0].default_value = 1
                        intensify.inputs[1].default_value = intensity
                        material_tree.links.new \
                          (
                            input_terminal,
                            intensify.inputs[0]
                          )
                        output_terminal = intensify.outputs[0]
                    #end if
                #end if
                return \
                    output_terminal
            #end add_intensity_nodes

            def add_bump_convert_nodes(texture_output, extra_nodes_location) :
                # adds a node for converting a bump map to a normal map.
                bump_convert = material_tree.nodes.new("ShaderNodeBump")
                bump_convert.location = extra_nodes_location
                intensity = settings.bumpmapIntensity
                if intensity != 1 :
                    bump_convert.inputs["Strength"].default_value = intensity
                #end if
                material_tree.links.new \
                  (
                    texture_output,
                    bump_convert.inputs["Height"]
                  )
                return \
                    bump_convert.outputs["Normal"]
            #end add_bump_convert_nodes

            def add_normal_mapping_nodes(texture_output, extra_nodes_location) :
                # adds a node for correctly applying the normal map.
                map = material_tree.nodes.new("ShaderNodeNormalMap")
                map.location = extra_nodes_location
                intensity = settings.normalmapIntensity
                if intensity != 1 :
                    map.inputs["Strength"].default_value = intensity
                #end if
                material_tree.links.new \
                  (
                    texture_output,
                    map.inputs["Color"]
                  )
                return \
                    map.outputs["Normal"]
            #end add_normal_mapping_nodes

            add_special_nodes_for = \
                {
                    MAP.BUMP : add_bump_convert_nodes,
                    MAP.NORMAL : add_normal_mapping_nodes,
                }
            got_transparency = settings.opacity < 1
            diffuse_map_node = None
            for map in (MAP.DIFFUSE, MAP.SPECULAR, MAP.ALPHA, MAP.NORMAL, MAP.BUMP) :
              # Go according to ordering of input nodes on Principled BSDF,
              # to avoid wires crossing.
                if getattr(settings, map.map_name) != None :
                    extra_nodes_location = list(map_location)
                    extra_nodes_location[0] += 300
                    tex_image = new_image_texture_node(map)
                    if map == MAP.ALPHA or map == MAP.DIFFUSE and tex_image.image.channels > 3 :
                        # pointless check: tex_image.image.channels returns 4 even when
                        # loading RGB (not RGBA) PNG image
                        got_transparency = True
                        if map == MAP.DIFFUSE :
                            diffuse_map_node = tex_image
                        #end if
                    #end if
                    add_special_nodes = add_special_nodes_for.get(map)
                    output_terminal = tex_image.outputs["Color"]
                    if add_special_nodes != None :
                        output_terminal = add_special_nodes(output_terminal, extra_nodes_location)
                    else :
                        output_terminal = add_intensity_nodes \
                            (
                                map,
                                output_terminal,
                                extra_nodes_location
                            )
                    #end if
                    material_tree.links.new \
                      (
                        output_terminal,
                        main_shader.inputs[map.principled_bsdf_input_name]
                      )
                #end if
            #end for
            if (
                    got_transparency
                and
                    settings.transparencymapTexture == None
                and
                    diffuse_map_node != None
            ) :
                material_tree.links.new \
                  (
                    diffuse_map_node.outputs["Alpha"],
                    main_shader.inputs["Alpha"]
                  )
            #end if
            if settings.displacementmapTexture != None :
                tex_image = new_image_texture_node(MAP.DISPLACEMENT)
                if tex_image.image.channels > 3 :
                    got_transparency = True
                #end if
                extra_nodes_location = list(map_location)
                extra_nodes_location[0] += 300
                material_tree.links.new \
                  (
                    add_intensity_nodes
                      (
                        MAP.DISPLACEMENT,
                        tex_image.outputs["Color"],
                        extra_nodes_location
                      ),
                    material_output.inputs["Displacement"]
                  )
                material.cycles.displacement_method = "BOTH"
                  # values are "BUMP" (default), "DISPLACEMENT" or "BOTH"
            #end if
            if got_transparency :
                material.blend_method = "BLEND"
            #end if
            deselect_all(material_tree)
            # all done
            status = {"FINISHED"}
        except Failure as why :
            sys.stderr.write("Failure: %s\n" % why.msg) # debug
            self.report({"ERROR"}, why.msg)
            status = {"CANCELLED"}
        #end try
        return \
            status
    #end execute

#end ImportMakeHumanMaterial

#+
# Mainline
#-

def add_invoke_item(self, context) :
    self.layout.operator(ImportMakeHumanMaterial.bl_idname, text = "MakeHuman Material")
#end add_invoke_item

_classes_ = \
    (
        ImportMakeHumanMaterial,
    )

def register() :
    for ċlass in _classes_ :
        bpy.utils.register_class(ċlass)
    #end for
    bpy.types.TOPBAR_MT_file_import.append(add_invoke_item)
#end register

def unregister() :
    bpy.types.TOPBAR_MT_file_import.remove(add_invoke_item)
    for ċlass in _classes_ :
        bpy.utils.unregister_class(ċlass)
    #end for
#end unregister

if __name__ == "__main__" :
    register()
#end if
