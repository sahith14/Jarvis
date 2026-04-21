import * as THREE from "three";

export type OrbState = "idle" | "listening" | "thinking" | "speaking";

export function createOrb(canvas: HTMLCanvasElement) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x050508);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
  camera.position.z = 60;

  const N = 1500;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  const colors = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    const r = 15 + Math.random() * 20;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    pos[i*3] = r * Math.sin(phi) * Math.cos(theta);
    pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    pos[i*3+2] = r * Math.cos(phi);
    colors[i*3] = 0.3 + 0.7 * Math.random();
    colors[i*3+1] = 0.5 + 0.5 * Math.random();
    colors[i*3+2] = 1.0;
  }
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.25,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const points = new THREE.Points(geo, mat);
  scene.add(points);

  let state: OrbState = "idle";
  let time = 0;

  function animate() {
    requestAnimationFrame(animate);
    time += 0.005;
    const positions = geo.attributes.position.array as Float32Array;
    for (let i = 0; i < N; i++) {
      const i3 = i * 3;
      const x = positions[i3], y = positions[i3+1], z = positions[i3+2];
      // subtle movement
      const noise = Math.sin(time + i) * 0.02;
      positions[i3] = x + (y * 0.01) * Math.sin(time) + noise;
      positions[i3+1] = y + (z * 0.01) * Math.cos(time*0.7) + noise;
      positions[i3+2] = z + (x * 0.01) * Math.sin(time*0.5) + noise;
    }
    geo.attributes.position.needsUpdate = true;
    points.rotation.y += 0.001;
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  return {
    setState(s: OrbState) { state = s; },
    destroy() { renderer.dispose(); }
  };
}
