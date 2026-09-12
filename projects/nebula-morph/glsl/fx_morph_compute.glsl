// fx_morph compute shader - nebula-morph
// Positionne chaque particule sur la forme cible (sphere, tore, galaxie
// spirale, grille d'onde) en fonction des signaux de controle, et calcule
// la couleur par particule (palette + pseudo-profondeur radiale).
// Les identifiants stables viennent de l'attribut Seed (src_particles).

uniform float u_shapetarget;  // 0..1 sur 4 formes (index / 3)
uniform float u_morph;        // 0..1 progression de transition
uniform float u_chaos;        // 0..1 intensite du chaos
uniform float u_palettephase; // 0..1 phase de palette
uniform float u_paletteshift; // 0..1 decalage utilisateur de teinte

const float TAU = 6.28318530718;
const float PI = 3.14159265359;

vec3 shapePos(int idx, float u, float v, float r1, float r2) {
    if (idx == 0) {
        // sphere
        float th = u * TAU;
        float ph = v * PI;
        float R = 1.02 + 0.14 * (r1 - 0.5);
        return R * vec3(cos(th) * sin(ph), 0.92 * cos(ph), sin(th) * sin(ph));
    } else if (idx == 1) {
        // tore
        float th = u * TAU;
        float ph = v * TAU;
        float R = 0.82;
        float r = 0.30 + 0.12 * (r2 - 0.5);
        return vec3((R + r * cos(ph)) * cos(th), r * sin(ph), (R + r * cos(ph)) * sin(th));
    } else if (idx == 2) {
        // galaxie spirale, 3 bras
        float rad = 0.10 + 0.98 * sqrt(v);
        float arm = floor(u * 3.0);
        float ang = rad * 3.4 + arm * (TAU / 3.0) + (r1 - 0.5) * 0.9;
        float thick = (r2 - 0.5) * 0.24 * (1.25 - rad * 0.45);
        return vec3(rad * cos(ang), thick, rad * sin(ang));
    }
    // grille d'onde
    float x = (u - 0.5) * 3.4;
    float z = (v - 0.5) * 3.4;
    float y = 0.40 * sin(x * 2.4) * cos(z * 2.4);
    return vec3(x, y, z);
}

vec3 nebulaPalette(float t) {
    vec3 deep = vec3(0.07, 0.16, 0.48);
    vec3 violet = vec3(0.38, 0.20, 0.70);
    vec3 warm = vec3(1.00, 0.56, 0.30);
    t = clamp(t, 0.0, 1.0);
    if (t < 0.62) return mix(deep, violet, t / 0.62);
    return mix(violet, warm, (t - 0.62) / 0.38);
}

vec3 hueShift(vec3 color, float amount) {
    const mat3 toYIQ = mat3(
        0.299, 0.587, 0.114,
        0.596, -0.274, -0.322,
        0.211, -0.523, 0.312
    );
    const mat3 toRGB = mat3(
        1.0, 0.956, 0.621,
        1.0, -0.272, -0.647,
        1.0, -1.106, 1.703
    );
    vec3 yiq = toYIQ * color;
    float angle = atan(yiq.z, yiq.y) + amount * TAU;
    float chroma = length(yiq.yz);
    yiq.y = chroma * cos(angle);
    yiq.z = chroma * sin(angle);
    return clamp(toRGB * yiq, 0.0, 1.0);
}

void main() {
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;

    vec3 src = TDIn_P();
    float seed = TDIn_Seed();

    // parametres stables par particule : u,v depuis la position source
    // + decorrelation par la graine
    float u = fract(src.x + 0.5 + seed * 0.61803398875);
    float v = clamp(fract(src.y + 0.5 + seed * 0.38196601125), 0.0, 1.0);
    float r1 = fract(seed * 127.1 + 0.37);
    float r2 = fract(seed * 311.7 + 0.71);

    int idxB = int(round(u_shapetarget * 3.0));
    int idxA = (idxB + 3) % 4;
    float t = smoothstep(0.0, 1.0, clamp(u_morph, 0.0, 1.0));
    vec3 pa = shapePos(idxA, u, v, r1, r2);
    vec3 pb = shapePos(idxB, u, v, r1, r2);
    vec3 pos = mix(pa, pb, t);

    // couleur : palette pilotee par la phase, pseudo-profondeur radiale,
    // scintillement par graine module par le chaos
    float f = fract(seed * 0.73 + u_palettephase);
    float glow = 0.34 + 0.66 * exp(-length(pos) * 1.35);
    float tw = 0.65 + 0.35 * fract(seed * 43.7 + u_chaos * seed);
    vec3 col = nebulaPalette(f) * glow * tw;
    col = hueShift(col, u_paletteshift);

    P[id] = pos;
    Color[id] = vec4(col, 1.0);
}
