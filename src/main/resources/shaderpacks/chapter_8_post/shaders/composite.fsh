#version 330 compatibility

/* RENDERTARGETS: 0 */

// ── EFFECT mode (injected by mod preset system) ──
// 0 = default (pass-through)
// 1 = bloom
// 2 = tonemap (3-panel comparison)
// 3 = color grading
// 4 = FXAA
// 5 = film look
#define EFFECT 0

uniform sampler2D colortex0;
uniform float viewWidth;
uniform float viewHeight;
uniform float frameTimeCounter;

in vec2 texcoord;

layout(location = 0) out vec4 outColor;

// ── ACES Tone Mapping ──
vec3 ACESFitted(vec3 x) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// ── Reinhard Tone Mapping ──
vec3 reinhard(vec3 x) {
    return x / (x + vec3(1.0));
}

// ── Luminance ──
float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

// ── Gaussian blur helpers (1D, 9-tap separable) ──
vec4 blurH(sampler2D tex, vec2 uv, vec2 texel) {
    float w[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec4 result = texture(tex, uv) * w[0];
    for (int i = 1; i < 5; i++) {
        result += texture(tex, uv + vec2(texel.x * float(i), 0.0)) * w[i];
        result += texture(tex, uv - vec2(texel.x * float(i), 0.0)) * w[i];
    }
    return result;
}

vec4 blurV(sampler2D tex, vec2 uv, vec2 texel) {
    float w[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec4 result = texture(tex, uv) * w[0];
    for (int i = 1; i < 5; i++) {
        result += texture(tex, uv + vec2(0.0, texel.y * float(i))) * w[i];
        result += texture(tex, uv - vec2(0.0, texel.y * float(i))) * w[i];
    }
    return result;
}

// ── Bloom per-pixel ──
vec3 applyBloom(sampler2D tex, vec2 uv, vec2 texel) {
    vec3 color = texture(tex, uv).rgb;
    float lum = luminance(color);
    float brightness = smoothstep(0.4, 1.0, lum);

    vec4 blurHV = blurV(tex, uv, texel * 2.0);
    vec3 bloom = max(vec3(0.0), blurHV.rgb * brightness * 0.55);

    return color + bloom;
}

// ── Color grading: saturation boost + warm tint ──
vec3 colorGrade(vec3 c) {
    float lum = luminance(c);
    c = mix(vec3(lum), c, 1.35);
    c = c * vec3(1.08, 0.95, 0.86);
    return c;
}

// ── FXAA 3.11 (simplified) ──
float rgb2luma(vec3 rgb) {
    return dot(rgb, vec3(0.299, 0.587, 0.114));
}

vec3 applyFXAA(sampler2D tex, vec2 uv, vec2 texel) {
    const float FXAA_SPAN_MAX = 8.0;
    const float FXAA_REDUCE_MUL = 1.0 / 8.0;
    const float FXAA_REDUCE_MIN = 1.0 / 128.0;

    vec3 rgbNW = texture(tex, uv + vec2(-1.0, -1.0) * texel).rgb;
    vec3 rgbNE = texture(tex, uv + vec2(1.0, -1.0) * texel).rgb;
    vec3 rgbSW = texture(tex, uv + vec2(-1.0, 1.0) * texel).rgb;
    vec3 rgbSE = texture(tex, uv + vec2(1.0, 1.0) * texel).rgb;
    vec3 rgbM  = texture(tex, uv).rgb;

    float lumaNW = rgb2luma(rgbNW);
    float lumaNE = rgb2luma(rgbNE);
    float lumaSW = rgb2luma(rgbSW);
    float lumaSE = rgb2luma(rgbSE);
    float lumaM  = rgb2luma(rgbM);

    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));
    float lumaRange = lumaMax - lumaMin;

    if (lumaRange < max(FXAA_REDUCE_MIN, lumaMax * FXAA_REDUCE_MUL)) return rgbM;

    vec2 dir = vec2(
        -((lumaNW + lumaNE) - (lumaSW + lumaSE)),
         ((lumaNW + lumaSW) - (lumaNE + lumaSE))
    );
    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * 0.03125, FXAA_REDUCE_MIN);
    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = min(vec2(FXAA_SPAN_MAX), max(vec2(-FXAA_SPAN_MAX), dir * rcpDirMin)) * texel;

    vec3 rgbA = 0.5 * (
        texture(tex, uv + dir * (1.0 / 3.0 - 0.5)).rgb +
        texture(tex, uv + dir * (2.0 / 3.0 - 0.5)).rgb
    );
    vec3 rgbB = rgbA * 0.5 + 0.25 * (
        texture(tex, uv + dir * -0.5).rgb +
        texture(tex, uv + dir * 0.5).rgb
    );
    float lumaB = rgb2luma(rgbB);
    if (lumaB < lumaMin || lumaB > lumaMax) return rgbA;
    return rgbB;
}

// ── Vignette ──
float vignette(vec2 uv) {
    vec2 d = abs(uv - 0.5) * 2.0;
    return 1.0 - dot(d, d) * 0.38;
}

// ── Film look: combined pipeline ──
vec3 filmLook(vec3 c, vec2 uv) {
    c = ACESFitted(c * 1.2);
    c = c * vec3(1.08, 0.94, 0.86);
    c *= vignette(uv);
    return c;
}

// ─── MAIN ───────────────────────────────────────────────────────
void main() {
    vec3 color = texture(colortex0, texcoord).rgb;
    vec2 texel = 1.0 / vec2(viewWidth, viewHeight);
    vec3 result;

#if EFFECT == 1
    // ── Bloom: left=original, right=bloom ──
    if (texcoord.x < 0.5) {
        result = color;
    } else {
        vec2 rightUV = (texcoord - vec2(0.5, 0.0)) * vec2(2.0, 1.0);
        result = applyBloom(colortex0, rightUV, texel);
    }
    if (abs(texcoord.x - 0.5) < 0.003) result = vec3(1.0);

#elif EFFECT == 2
    // ── Tonemap: 3 panels ──
    float third = 1.0 / 3.0;
    if (texcoord.x < third) {
        result = color;
    } else if (texcoord.x < 2.0 * third) {
        result = reinhard(color);
    } else {
        result = ACESFitted(color);
    }
    if (abs(texcoord.x - third) < 0.0025 || abs(texcoord.x - 2.0 * third) < 0.0025)
        result = vec3(1.0);

#elif EFFECT == 3
    // ── Color Grade: left=original, right=graded ──
    if (texcoord.x < 0.5) {
        result = color;
    } else {
        result = colorGrade(color);
    }
    if (abs(texcoord.x - 0.5) < 0.003) result = vec3(1.0);

#elif EFFECT == 4
    // ── FXAA: left=no AA, right=FXAA ──
    if (texcoord.x < 0.5) {
        result = color;
    } else {
        result = applyFXAA(colortex0, texcoord, texel);
    }
    if (abs(texcoord.x - 0.5) < 0.003) result = vec3(1.0);

#elif EFFECT == 5
    // ── Film Look: full screen ──
    result = filmLook(color, texcoord);

#else
    // ── Default: pass-through ──
    result = color;
#endif

    outColor = vec4(result, 1.0);
}