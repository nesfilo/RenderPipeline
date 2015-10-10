#pragma once

#pragma include "Includes/Configuration.inc.glsl"


vec3 lambertianBRDF(vec3 diffuse, float NxL) {
    return  diffuse * NxL / M_PI;
}


// GGX / Trowbridge-Reitz
// [Walter et al. 2007, "Microfacet models for refraction through rough surfaces"]
float D_GGX( float Roughness, float NxH )
{
    // Anything less than 0.05 just produces artifacts
    Roughness = max(Roughness, 0.05);
    float m = Roughness * Roughness;
    float m2 = m * m;
    float d = ( NxH * m2 - NxH ) * NxH + 1; // 2 mad
    return m2 / ( M_PI*d*d );                 // 4 mul, 1 rcp
}

// Tuned to match behavior of Vis_Smith
// [Schlick 1994, "An Inexpensive BRDF Model for Physically-Based Rendering"]
float Vis_Schlick( float Roughness, float NxV, float NxL )
{
    float k = Roughness * Roughness * 0.5;
    float Vis_SchlickV = NxV * (1 - k) + k;
    float Vis_SchlickL = NxL * (1 - k) + k;
    return 0.25 / ( Vis_SchlickV * Vis_SchlickL );
}


// Appoximation of joint Smith term for GGX
// [Heitz 2014, "Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs"]
float Vis_SmithJointApprox( float Roughness, float NxV, float NxL )
{
    float a = Roughness * Roughness;
    float Vis_SmithV = NxL * ( NxV * ( 1 - a ) + a );
    float Vis_SmithL = NxV * ( NxL * ( 1 - a ) + a );
    return 0.5 / ( Vis_SmithV + Vis_SmithL );
}

// [Schlick 1994, "An Inexpensive BRDF Model for Physically-Based Rendering"]
// [Lagarde 2012, "Spherical Gaussian approximation for Blinn-Phong, Phong and Fresnel"]
vec3 F_Schlick( vec3 SpecularColor, float VxH )
{
    float Fc = pow(VxH, 5 );  

    return Fc * SpecularColor;                         // 1 sub, 3 mul
    //float Fc = exp2( (-5.55473 * VoH - 6.98316) * VoH );  // 1 mad, 1 mul, 1 exp
    //return Fc + (1 - Fc) * SpecularColor;                 // 1 add, 3 mad
    
    // Anything less than 2% is physically impossible and is instead considered to be shadowing
    // return (1.0 - Fc) * SpecularColor;
    // return Fc + SpecularColor - Fc * SpecularColor;
    // return vec3(Fc); 
    // return saturate( 50.0 * SpecularColor.g ) * Fc + (1 - Fc) * SpecularColor;
    
}




float Distribution( float Roughness, float NxH )
{

    return D_GGX(Roughness, NxH);
// #if   PHYSICAL_SPEC_D == 0
//     return D_Blinn( Roughness, NoH );
// #elif PHYSICAL_SPEC_D == 1
//     return D_Beckmann( Roughness, NoH );
// #elif PHYSICAL_SPEC_D == 2
//     return D_GGX( Roughness, NoH );
// #endif
}

// Vis = G / (4*NoL*NoV)
float GeometricVisibility( float Roughness, float NxV, float NxL, float VxH )
{
    // return 1.0;
// #if   PHYSICAL_SPEC_G == 0
//     return Vis_Implicit();
// #elif PHYSICAL_SPEC_G == 1
//     return Vis_Neumann( NoV, NoL );
// #elif PHYSICAL_SPEC_G == 2
//     return Vis_Kelemen( VoH );
// #elif PHYSICAL_SPEC_G == 3
    // return Vis_Schlick( Roughness, NxV, NxL );
    return Vis_SmithJointApprox( Roughness, NxV, NxL );
// #elif PHYSICAL_SPEC_G == 4
//     return Vis_Smith( Roughness, NoV, NoL );
// #endif
}

vec3 Fresnel( vec3 SpecularColor, float VxH )
{
// #if   PHYSICAL_SPEC_F == 0
//     return F_None( SpecularColor );
// #elif PHYSICAL_SPEC_F == 1
    return F_Schlick( SpecularColor, VxH );
// #elif PHYSICAL_SPEC_F == 2
//     return F_Fresnel( SpecularColor, VoH );
// #endif
}