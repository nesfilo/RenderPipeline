#version 430

#define IS_GBUFFER_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

layout(location=0) in VertexOutput vOutput;

uniform sampler2D p3d_Texture0;

uniform float roughness;
uniform float specular;

void main() {

    vec4 diffuseSample = texture(p3d_Texture0, vOutput.texcoord);

    Material m;
    m.diffuse = diffuseSample.xyz;
    m.normal = vOutput.normal;
    m.position = vOutput.position;
    m.metallic = 0;
    m.specular = specular;
    m.roughness = roughness;



    render_material(m);
}

