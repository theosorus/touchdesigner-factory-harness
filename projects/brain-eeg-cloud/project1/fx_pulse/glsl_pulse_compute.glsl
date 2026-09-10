// fx_pulse -- breathing, activity focus, lighting and colour of the brain point cloud.
//
// The cloud comes from a SURFACE mesh, so every point carries the real normal of the
// cortical skin. Three depth cues follow from that, and it is their absence that made
// the rotation direction ambiguous (kinetic depth ambiguity, the Necker cube family):
//   1. the back face is REMOVED, not dimmed;
//   2. brightness decreases with distance to the camera;
//   3. the lighting model rotates with the object.
// Depth-buffer occlusion, the fourth cue, is a setting on the MAT.
//
// Uniforms provided by the GLSL POP's vec sequence:
//   uSignal = (alpha, beta, theta, 0)
//   uCtrl   = (Breath, Dispersion, Warmth, time in seconds)
//   uZone   = (focus travel period, Zonesize, Activity, 0)
//   uCam    = (camera xyz position, Depthfade)
// In: P, N, Seed (0-1, unique per point). Out: displaced P and premultiplied Color.

vec3 hash3(float n)
{
	return fract(sin(vec3(n, n + 1.7, n + 3.3)) * vec3(43758.5453, 22578.1459, 19642.3490)) * 2.0 - 1.0;
}

// Centre of the activity focus: it jumps to a new position every period, with a smooth
// interpolation so the move reads as a propagation rather than a cut.
vec3 zoneCenter(float t, float period)
{
	float slot = floor(t / period);
	float f = smoothstep(0.0, 1.0, fract(t / period));
	vec3 a = hash3(slot * 11.0 + 3.0);
	vec3 b = hash3((slot + 1.0) * 11.0 + 3.0);
	return mix(a, b, f) * vec3(0.62, 0.60, 0.85);
}

void main()
{
	const uint id = TDIndex();
	if (id >= TDNumElements())
		return;

	vec3 p = TDIn_P();
	vec3 n = normalize(TDIn_N());
	float seed = TDIn_Seed();

	float alpha = uSignal.x;
	float beta = uSignal.y;
	float theta = uSignal.z;
	float breathAmt = uCtrl.x;
	float disperseAmt = uCtrl.y;
	float violetAmt = uCtrl.z;
	float t = uCtrl.w;
	float zonePeriod = max(uZone.x, 0.5);
	float zoneRadius = max(uZone.y, 0.05);
	float activityAmt = uZone.z;
	vec3 camPos = uCam.xyz;
	float depthFade = uCam.w;

	// Breathing: the surface swells along its own normal, phase-shifted per point.
	float phase = seed * 6.2831853;
	float slow = sin(t * 0.55 + phase);
	float fast = sin(t * 1.70 + phase * 2.3);
	float breath = 0.5 + 0.5 * (0.75 * slow + 0.25 * fast);
	float amp = breathAmt * 0.09 * (0.35 + 0.65 * alpha);
	vec3 disp = n * amp * breath;

	// One activity focus at a time: it travels through the volume and breathes on its own
	// rhythm. Nearby points light up and are pushed outward.
	vec3 zc = zoneCenter(t, zonePeriod);
	float zd = length(p - zc);
	float zw = exp(-(zd * zd) / (zoneRadius * zoneRadius));
	float pulse = 0.45 + 0.55 * (0.5 + 0.5 * sin(t * 1.25));
	float act = clamp(zw * pulse * 2.1 * activityAmt * (0.35 + 0.65 * beta), 0.0, 1.0);
	disp += n * act * 0.05;

	// Dispersion: only real beta peaks throw points out (beta squared).
	vec3 jitter = hash3(seed * 512.0 + 3.0);
	float burst = disperseAmt * beta * beta;
	disp += jitter * burst * 0.30 * (0.35 + 0.65 * seed);

	vec3 pFinal = p + disp;
	P[id] = pFinal;

	vec3 toCam = normalize(camPos - pFinal);
	float facing = dot(n, toCam);

	// CUE 1: the back face disappears. A point facing away from the camera is not dimmed,
	// it is not drawn at all. With no visible back face there are no longer two possible
	// readings of the rotation direction.
	if (facing < 0.02 * depthFade) {
		Color[id] = vec4(0.0);
		return;
	}
	float faceMask = smoothstep(0.0, 0.30, facing);

	// CUE 2: distance to the camera. Near is bright, far is dark, monotonically, which
	// gives a readable depth order during the rotation.
	float camRadius = length(camPos);
	float dist01 = clamp((length(pFinal - camPos) - (camRadius - 1.35)) / 2.70, 0.0, 1.0);
	float depthCue = mix(1.0, 0.15 + 0.85 * (1.0 - dist01) * (1.0 - dist01), depthFade);

	// CUE 3: lighting. A warm key top-left, a cool fill on the other side, Fresnel on the
	// rims. The model turns with the object, so it confirms the rotation direction instead
	// of leaving it floating.
	vec3 keyDir = normalize(vec3(-0.45, 0.75, 0.50));
	vec3 fillDir = normalize(vec3(0.65, -0.25, 0.30));
	float key = max(dot(n, keyDir), 0.0);
	float fill = max(dot(n, fillDir), 0.0);
	float fresnel = pow(1.0 - clamp(facing, 0.0, 1.0), 2.2);
	float shade = 0.18 + 0.92 * key + 0.22 * fill + 0.85 * fresnel;

	// Palette: pale pink dominant, light violet detail, amber activity focus.
	vec3 rose = vec3(1.00, 0.62, 0.78);
	vec3 violet = vec3(0.74, 0.55, 0.98);
	vec3 amber = vec3(1.00, 0.66, 0.20);

	// Violet marks the sulci -- where the normal turns away from the key light -- while
	// the ridges stay pink.
	float violetMix = clamp(violetAmt * (0.25 * seed + 1.25 * (1.0 - key)), 0.0, 1.0);
	vec3 col = mix(rose, violet, violetMix);
	col = mix(col, amber, smoothstep(0.02, 0.55, act));

	float bright = 0.030 + 0.055 * breath * (0.35 + 0.65 * alpha);
	bright *= shade;
	bright *= 0.70 + 0.60 * seed;
	bright *= mix(1.0, 0.03 + 0.97 * faceMask, depthFade) * depthCue;
	bright += act * 0.26 * mix(1.0, 0.25 + 0.75 * faceMask, depthFade);

	// Alpha = the strongest channel of the emitted colour. Premultiplied, so a dark point
	// never occludes the background: no black halo around the brain.
	vec3 rgb = col * bright;
	float a = clamp(max(max(rgb.r, rgb.g), rgb.b), 0.0, 1.0);
	Color[id] = vec4(rgb, a);
}
