/* The few parts of three.js (decision D1) the home page's hero uses, typed by hand: three ships no type definitions of
   its own, and `@types/three` is a separate download (D1b). Only what the hero calls is declared. */
declare module "three" {
  export const NormalBlending: number;

  export class Color {
    constructor(r: number, g: number, b: number);
  }

  export class BufferAttribute {
    constructor(array: Float32Array, itemSize: number);
  }

  export class BufferGeometry {
    setAttribute(name: string, attribute: BufferAttribute): this;
    dispose(): void;
  }

  export interface Uniform<T> {
    value: T;
  }

  export class ShaderMaterial {
    constructor(parameters: {
      uniforms: Record<string, Uniform<unknown>>;
      vertexShader: string;
      fragmentShader: string;
      transparent?: boolean;
      depthWrite?: boolean;
      blending?: number;
    });
    uniforms: Record<string, Uniform<unknown>>;
    dispose(): void;
  }

  export class Object3D {
    rotation: { x: number; y: number; z: number };
  }

  export class Points extends Object3D {
    constructor(geometry: BufferGeometry, material: ShaderMaterial);
  }

  export class Scene extends Object3D {
    add(object: Object3D): this;
  }

  export class PerspectiveCamera extends Object3D {
    constructor(fov: number, aspect: number, near: number, far: number);
    aspect: number;
    position: { set(x: number, y: number, z: number): void };
    updateProjectionMatrix(): void;
  }

  export class WebGLRenderer {
    constructor(parameters: { canvas: HTMLCanvasElement; alpha?: boolean; antialias?: boolean });
    setPixelRatio(ratio: number): void;
    setSize(width: number, height: number, updateStyle?: boolean): void;
    render(scene: Scene, camera: PerspectiveCamera): void;
    dispose(): void;
  }
}
