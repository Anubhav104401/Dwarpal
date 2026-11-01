/** The home page's 3D hero (decision D1): a face drawn as points of light. The face is no one's: its shape is made
 * here from a few smooth rules — an egg-shaped head, a nose, eye hollows, lips and a narrower chin — never from a
 * person's face, which would be biometric data. */

/** As many points as the face mesh the verify page's guidance tracks (MediaPipe's 478 landmarks). */
export const FACE_POINTS = 478;

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

/** A smooth bump: 1 at its centre, falling to almost 0 a few `width`s away. */
function bump(x: number, y: number, cx: number, cy: number, wx: number, wy: number): number {
  return Math.exp(-(((x - cx) / wx) ** 2 + ((y - cy) / wy) ** 2));
}

/**
 * The points as one flat list — x, y, z for each — in a box about 2 units tall, the face looking along +z.
 *
 * The points start evenly spread over the front of a sphere (a *Fibonacci lattice*: each point a golden angle round
 * from the one before, so no two crowd together), and the sphere is then pressed into the shape of a face.
 */
export function facePoints(count: number = FACE_POINTS): Float32Array {
  const points = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    // Heights from top to bottom over the front of the sphere, and the angle round it.
    const y = 1 - (2 * (i + 0.5)) / count;
    const ring = Math.sqrt(1 - y * y);
    const turn = i * GOLDEN_ANGLE;
    let x = Math.cos(turn) * ring;
    let z = Math.abs(Math.sin(turn)) * ring; // the front half only: a face, not a head

    // An egg: narrower than tall, flatter than wide, and narrowing towards the chin.
    x *= 0.74 * (1 - 0.22 * Math.max(0, -y) ** 2);
    z *= 0.6;
    // A nose down the middle, hollows for the eyes, a little fullness for the lips.
    z += 0.3 * bump(x, y, 0, -0.08, 0.11, 0.3);
    z -= 0.12 * (bump(x, y, -0.3, 0.22, 0.13, 0.08) + bump(x, y, 0.3, 0.22, 0.13, 0.08));
    z += 0.06 * bump(x, y, 0, -0.5, 0.2, 0.06);

    points.set([x, y, z], i * 3);
  }
  return points;
}
