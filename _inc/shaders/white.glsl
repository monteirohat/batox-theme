// Draws an image in white, keeping its shape: the home's system logos, which are Batocera's own
// colored ones (Carbon's), become white like a console home's.
//
//   cutDark  0 (default): every visible pixel turns white (the logo's silhouette).
//            0.1 to 0.5: pixels darker than this also turn transparent, for logos drawn on a
//            dark plate (Mega Drive, Game Boy Advance...), whose silhouette would be a blob.
//
// The element's <color> and opacity still apply.

#if defined(VERTEX)

#if __VERSION__ >= 130
#define COMPAT_VARYING out
#define COMPAT_ATTRIBUTE in
#else
#define COMPAT_VARYING varying
#define COMPAT_ATTRIBUTE attribute
#endif

uniform mat4 MVPMatrix;
COMPAT_ATTRIBUTE vec2 VertexCoord;
COMPAT_ATTRIBUTE vec2 TexCoord;
COMPAT_ATTRIBUTE vec4 COLOR;
COMPAT_VARYING vec2 v_tex;
COMPAT_VARYING vec4 v_col;

void main(void)
{
	gl_Position = MVPMatrix * vec4(VertexCoord.xy, 0.0, 1.0);
	v_tex = TexCoord;
	v_col = COLOR;
}

#elif defined(FRAGMENT)

#if __VERSION__ >= 130
#define COMPAT_VARYING in
#define COMPAT_TEXTURE texture
out vec4 FragColor;
#else
#define COMPAT_VARYING varying
#define FragColor gl_FragColor
#define COMPAT_TEXTURE texture2D
#endif

#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
#endif

COMPAT_VARYING vec4 v_col;
COMPAT_VARYING vec2 v_tex;
uniform sampler2D u_tex;
uniform COMPAT_PRECISION float cutDark;

void main(void)
{
	vec4 tex = COMPAT_TEXTURE(u_tex, v_tex);
	float alpha = tex.a;
	if (cutDark > 0.0)
	{
		// Undo the premultiplication, if any, before judging how dark the pixel is
		vec3 rgb = tex.a > 0.0 ? tex.rgb / max(tex.a, 0.001) : tex.rgb;
		float luma = dot(min(rgb, vec3(1.0)), vec3(0.299, 0.587, 0.114));
		alpha *= smoothstep(cutDark - 0.08, cutDark + 0.08, luma);
	}
	FragColor = vec4(1.0, 1.0, 1.0, alpha) * v_col;
}
#endif
