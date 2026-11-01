/* The hero's 3D scene (decision D1), loaded only in the browser and only when it will be shown: 478 points of light
   in the shape of a face, turning gently, crossed by a line of light as a check would, and now and then scattering and
   gathering again — the photos are taken, checked and let go. */

import {
  BufferAttribute,
  BufferGeometry,
  Color,
  NormalBlending,
  PerspectiveCamera,
  Points,
  Scene,
  ShaderMaterial,
  WebGLRenderer,
} from "three";

import { facePoints } from "@/lib/face-cloud";

/** Runs on the graphics card, once per point: where it goes, how big it is, and how much the scan line lights it. */
const VERTEX = /* glsl */ `
  uniform float scan;
  uniform float scatter;
  uniform float size;
  attribute float seed;
  varying float glow;
  varying float shade;
  void main() {
    // Nearer parts of the face (the nose, the cheeks) are brighter than the eye hollows and the edges.
    shade = clamp(0.35 + position.z * 1.1, 0.25, 1.0);
    // Scattering pushes each point outwards along its own direction, by its own amount.
    vec3 drift = normalize(position + vec3(0.0, 0.0, 0.3)) * scatter * (0.4 + seed);
    vec4 placed = modelViewMatrix * vec4(position + drift, 1.0);
    glow = smoothstep(0.12, 0.0, abs(position.y - scan));
    gl_PointSize = size * (1.0 + 1.5 * glow) / -placed.z;
    gl_Position = projectionMatrix * placed;
  }
`;

/** Runs once per pixel of each point: a soft round dot, the scan line's colour where it is lit. */
const FRAGMENT = /* glsl */ `
  uniform vec3 base;
  uniform vec3 light;
  varying float glow;
  varying float shade;
  void main() {
    float edge = length(gl_PointCoord - 0.5);
    if (edge > 0.5) discard;
    float alpha = smoothstep(0.5, 0.15, edge) * max(shade, glow);
    gl_FragColor = vec4(mix(base, light, glow), alpha);
  }
`;

/** A CSS colour (the design's tokens are written in OKLCH) as three numbers from 0 to 1: drawn into one pixel, which
 * the browser converts for us, then read back. */
function rgb(css: string): Color {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (context === null) {
    return new Color(0.5, 0.5, 0.5);
  }
  context.fillStyle = css;
  context.fillRect(0, 0, 1, 1);
  const [r = 128, g = 128, b = 128] = context.getImageData(0, 0, 1, 1).data;
  return new Color(r / 255, g / 255, b / 255);
}

/** A token's value, such as `--color-brand-500`, as the page has it. */
function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "gray";
}

/** Start the scene on `canvas`; the returned function stops it and frees everything it used. */
export function startFaceScene(canvas: HTMLCanvasElement): () => void {
  const renderer = new WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const positions = facePoints();
  const seeds = new Float32Array(positions.length / 3).map((_, i) => ((i * 0.618034) % 1) * 0.6);
  const geometry = new BufferGeometry()
    .setAttribute("position", new BufferAttribute(positions, 3))
    .setAttribute("seed", new BufferAttribute(seeds, 1));

  const dark = window.matchMedia("(prefers-color-scheme: dark)");
  const uniforms = {
    scan: { value: 0 },
    scatter: { value: 0 },
    size: { value: 0 },
    base: { value: rgb(token(dark.matches ? "--color-ink-300" : "--color-ink-600")) },
    light: { value: rgb(token("--color-brand-500")) },
  };
  const material = new ShaderMaterial({
    uniforms,
    vertexShader: VERTEX,
    fragmentShader: FRAGMENT,
    transparent: true,
    depthWrite: false,
    blending: NormalBlending,
  });
  const face = new Points(geometry, material);
  const scene = new Scene().add(face);
  const camera = new PerspectiveCamera(30, 1, 0.1, 20);
  camera.position.set(0, 0, 5.2);

  // Follow the canvas's size as the page is resized; the points' size follows its height.
  const resize = () => {
    const { clientWidth: width, clientHeight: height } = canvas;
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
    uniforms.size.value = height * 0.12 * Math.min(window.devicePixelRatio, 2);
  };
  const resizing = new ResizeObserver(resize);
  resizing.observe(canvas);
  resize();

  // Draw only while the hero is on screen and the tab is visible: no work for nobody.
  let visible = true;
  const watching = new IntersectionObserver(([entry]) => {
    visible = entry?.isIntersecting ?? true;
  });
  watching.observe(canvas);

  const started = performance.now();
  let frame = 0;
  const draw = (now: number) => {
    frame = requestAnimationFrame(draw);
    if (!visible || document.hidden) {
      return;
    }
    const t = (now - started) / 1000;
    face.rotation.y = 0.45 * Math.sin(t * 0.35);
    face.rotation.x = 0.08 * Math.sin(t * 0.23);
    uniforms.scan.value = 1.15 * Math.sin(t * 0.9);
    // Every 9 seconds: scatter for a moment, then gather again.
    const phase = (t % 9) / 9;
    uniforms.scatter.value = phase > 0.8 ? Math.sin(((phase - 0.8) / 0.2) * Math.PI) * 0.25 : 0;
    renderer.render(scene, camera);
  };
  frame = requestAnimationFrame(draw);

  return () => {
    cancelAnimationFrame(frame);
    resizing.disconnect();
    watching.disconnect();
    geometry.dispose();
    material.dispose();
    renderer.dispose();
  };
}
