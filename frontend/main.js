import * as THREE from 'three';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x96321e);
scene.fog = new THREE.Fog(0x96321e, 20, 150);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
hemiLight.position.set(0, 100, 0);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(-50, 50, 50);
dirLight.castShadow = true;
scene.add(dirLight);

// --- CELESTIAL ELEMENTS ---
const skyGroup = new THREE.Group();
scene.add(skyGroup);
const starGeo = new THREE.BufferGeometry();
const starPos = [];
for(let i=0; i<800; i++) {
    const x = (Math.random() - 0.5) * 800;
    const y = Math.random() * 300 + 50;
    const z = (Math.random() - 0.5) * 800;
    starPos.push(x, y, z);
}
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, transparent: true, opacity: 0, fog: false });
const stars = new THREE.Points(starGeo, starMat);
skyGroup.add(stars);

const phobos = new THREE.Mesh(new THREE.DodecahedronGeometry(12, 1), new THREE.MeshLambertMaterial({ color: 0xaaaaaa, emissive: 0x333333, transparent: true, opacity: 0, fog: false }));
phobos.position.set(-150, 120, -200);
skyGroup.add(phobos);

const deimos = new THREE.Mesh(new THREE.DodecahedronGeometry(6, 0), new THREE.MeshLambertMaterial({ color: 0x888888, emissive: 0x222222, transparent: true, opacity: 0, fog: false }));
deimos.position.set(180, 150, -150);
skyGroup.add(deimos);

// --- CYCLE ---
let timeOfDay = 0, targetColor = new THREE.Color(0x96321e), targetIntensity = 0.8, baseTemp = -40;
function updateCycle(dt) {
    timeOfDay += dt; if (timeOfDay >= 90) timeOfDay = 0;
    let night = timeOfDay >= 45;
    if (night) { targetColor.setHex(0x0a0f2b); targetIntensity = 0.15; baseTemp = -73; }
    else { targetColor.setHex(0x96321e); targetIntensity = 0.8; baseTemp = -40; }
    scene.background.lerp(targetColor, 0.5 * dt);
    scene.fog.color.lerp(targetColor, 0.5 * dt);
    dirLight.intensity += (targetIntensity - dirLight.intensity) * 0.5 * dt;
    hemiLight.intensity = dirLight.intensity * 0.75;
    let op = night ? 1 : 0;
    starMat.opacity += (op - starMat.opacity) * 0.5 * dt;
    phobos.material.opacity = starMat.opacity; deimos.material.opacity = starMat.opacity;
    phobos.position.applyAxisAngle(new THREE.Vector3(0,1,0), 0.05 * dt);
    deimos.position.applyAxisAngle(new THREE.Vector3(0,1,0), 0.02 * dt);
}

// --- TERRAIN ---
const terrainSize = 250;
const geometry = new THREE.PlaneGeometry(terrainSize, terrainSize, 64, 64);
geometry.rotateX(-Math.PI / 2);
function getGroundHeight(x, z) {
    return Math.sin(x / 10) * Math.cos(z / 10) * 2.5 + Math.sin(x / 5 + z / 3) * 1.5;
}
const posAttr = geometry.attributes.position;
for (let i = 0; i < posAttr.count; i++) {
    const x = posAttr.getX(i), z = posAttr.getZ(i);
    posAttr.setY(i, getGroundHeight(x, z));
}
geometry.computeVertexNormals();
const ground = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0xb45032, roughness: 0.9, flatShading: true }));
ground.receiveShadow = true;
scene.add(ground);

const rocks = [];
const rockGeo = new THREE.DodecahedronGeometry(1, 0);
const rockMat = new THREE.MeshStandardMaterial({ color: 0x64281e, roughness: 1, flatShading: true });
for (let i = 0; i < 110; i++) {
    const rx = (Math.random() - 0.5) * 180, rz = (Math.random() - 0.5) * 180;
    if (Math.abs(rx) < 15 && Math.abs(rz) < 15) continue;
    const r = new THREE.Mesh(rockGeo, rockMat);
    const s = Math.random() * 2 + 1.5;
    r.position.set(rx, getGroundHeight(rx, rz) + s * 0.5, rz);
    r.scale.set(s,s,s); r.rotation.set(Math.random()*3, Math.random()*3, Math.random()*3);
    r.castShadow = true; r.receiveShadow = true; scene.add(r); rocks.push(r);
}
// Crater
for (let a = 0; a < 6.3; a += 0.05) {
    const r = new THREE.Mesh(rockGeo, rockMat);
    const rx = Math.sin(a) * 120, rz = Math.cos(a) * 120, s = Math.random() * 5 + 10;
    r.position.set(rx, getGroundHeight(rx, rz) + s * 0.4, rz);
    r.scale.set(s, s*2, s); r.rotation.set(Math.random()*3, Math.random()*3, Math.random()*3);
    r.castShadow = true; r.receiveShadow = true; scene.add(r); rocks.push(r);
}

// --- ROVER ---
const rover = new THREE.Group();
rover.position.set(0, 5, 0); scene.add(rover);
const body = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.8, 2.5), new THREE.MeshStandardMaterial({ color: 0xffd700 }));
body.position.y = 1; body.castShadow = true; rover.add(body);
const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.5), new THREE.MeshStandardMaterial({ color: 0xaaaaaa }));
antenna.position.set(-0.4, 1.8, -0.4); rover.add(antenna);
const dish = new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 16), new THREE.MeshStandardMaterial({ color: 0xaaaaaa }));
dish.position.y = 0.75; antenna.add(dish);
const wheels = [];
const wOffsets = [[-1.2, 0.4, 1.3], [1.2, 0.4, 1.3], [-1.4, 0.4, 0], [1.4, 0.4, 0], [-1.2, 0.4, -1.3], [1.2, 0.4, -1.3]];
for (let o of wOffsets) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.4, 16), new THREE.MeshStandardMaterial({ color: 0x222222 }));
    w.rotateZ(Math.PI / 2); w.position.set(o[0], o[1], o[2]); w.castShadow = true;
    rover.add(w); wheels.push(w);
}

// --- LIDAR ---
const raycaster = new THREE.Raycaster();
const lidarLines = new THREE.Group(); rover.add(lidarLines);
const rays = [];
[0, 15, 30].forEach(p => { for (let y = -170; y <= 180; y += 10) rays.push({ yaw: y, pitch: p }); });
const mS = new THREE.LineBasicMaterial({ color: 0x00ff00 }), mH = new THREE.LineBasicMaterial({ color: 0xff0000 });
rays.forEach(() => {
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,15)]), mS);
    l.position.y = 0.5; lidarLines.add(l);
});

// --- STATE ---
let throttle = 0, steering = 0, manualT = 0, manualS = 0, aiT = 0, aiS = 0, override = false, lastS = 0;
let pH = 7.7, temp = -40, moist = 1.0;

document.addEventListener('keydown', e => {
    if (e.code === 'Space') override = true;
    if (override) {
        if (e.code === 'KeyW') manualT = 1; if (e.code === 'KeyS') manualT = -1;
        if (e.code === 'KeyA') manualS = 1; if (e.code === 'KeyD') manualS = -1;
    }
});
document.addEventListener('keyup', e => {
    if (e.code === 'Space') { override = false; manualT = 0; manualS = 0; }
    if (override) {
        if (e.code === 'KeyW' || e.code === 'KeyS') manualT = 0;
        if (e.code === 'KeyA' || e.code === 'KeyD') manualS = 0;
    }
});

let ws;
function connect() {
    ws = new WebSocket(window.location.hostname === 'localhost' ? 'ws://localhost:8000/ws' : 'wss://mars-rover-simulation.onrender.com/ws');
    ws.onmessage = e => { const d = JSON.parse(e.data); aiT = d.throttle; aiS = -d.steering; };
    ws.onclose = () => setTimeout(connect, 1000);
}
connect();

const clock = new THREE.Clock();

function updateCamera() {
    // FIXED CAMERA (NO LERP TO PREVENT FREEZE)
    const off = new THREE.Vector3(0, 10, -15).applyQuaternion(rover.quaternion).add(rover.position);
    camera.position.set(off.x, off.y, off.z);
    const trg = new THREE.Vector3(0, 2, 5).applyQuaternion(rover.quaternion).add(rover.position);
    camera.lookAt(trg); skyGroup.position.copy(camera.position);
}

function updatePhysics(dt) {
    let assist = false, brake = false;
    if (override) { throttle = manualT; steering = manualS; } else { throttle = aiT; steering = aiS; }

    if (throttle !== 0 || steering !== 0) {
        let block = false, haz = false;
        const sign = Math.sign(throttle) || 1;
        const rDir = new THREE.Vector3(0,0,1).applyAxisAngle(new THREE.Vector3(0,1,0), rover.rotation.y).multiplyScalar(sign);
        const offs = [new THREE.Vector3(0,0.8,0), new THREE.Vector3(0.7,0.8,0).applyAxisAngle(new THREE.Vector3(0,1,0), rover.rotation.y), new THREE.Vector3(-0.7,0.8,0).applyAxisAngle(new THREE.Vector3(0,1,0), rover.rotation.y)];
        for (let o of offs) {
            const hits = new THREE.Raycaster(rover.position.clone().add(o), rDir).intersectObjects(rocks);
            if (hits.length > 0) {
                const d = hits[0].distance;
                if (throttle > 0 && d < 6.0) haz = true;
                if (throttle < 0 && d < 2.5) { haz = true; brake = true; }
                if (d < 1.0) { block = true; break; }
            }
        }
        if (haz) { assist = true; throttle = 0; if (override) steering = aiS; }
        if (!block) {
            rover.rotation.y += steering * 5.0 * dt;
            const fwd = new THREE.Vector3(0,0,1).applyAxisAngle(new THREE.Vector3(0,1,0), rover.rotation.y);
            rover.position.addScaledVector(fwd, throttle * 4.0 * dt);
        }
    }
    rover.position.y = getGroundHeight(rover.position.x, rover.position.z);
    const fY = getGroundHeight(rover.position.x + Math.sin(rover.rotation.y)*2, rover.position.z + Math.cos(rover.rotation.y)*2);
    const bY = getGroundHeight(rover.position.x - Math.sin(rover.rotation.y)*2, rover.position.z - Math.cos(rover.rotation.y)*2);
    rover.rotation.x = Math.atan2(bY - fY, 4.0);

    const state = (ws && ws.readyState === 1) ? "Bağlandı" : "Bağlantı kesildi";
    let hud = `<h2>MARS ROVER</h2>Bağlantı: ${state}\nHız: ${throttle.toFixed(2)} | Dönüş: ${(-steering).toFixed(2)}\nSürüş: ${override ? 'MANUEL' : 'OTOPİLOT'}`;
    if (assist && override) hud += `<br><span style="color:#ff3333;">⚠️ KAZA ÖNLEYİCİ ${brake ? '(ARKA BRAK)' : '(ÖN ENGEL)'}</span>`;
    document.getElementById('hud').innerHTML = hud;
}

function processSensors(dt) {
    const pAll = [], sq = {};
    const orig = rover.position.clone(); orig.y += 0.5;
    rays.forEach((ray, i) => {
        const line = lidarLines.children[i];
        const yR = THREE.MathUtils.degToRad(ray.yaw), pR = THREE.MathUtils.degToRad(ray.pitch);
        const wDir = new THREE.Vector3(Math.sin(yR)*Math.cos(pR), Math.sin(pR), Math.cos(yR)*Math.cos(pR)).normalize().applyQuaternion(rover.quaternion);
        raycaster.set(orig, wDir);
        const hits = raycaster.intersectObjects(rocks);
        line.rotation.y = yR; line.rotation.x = -pR;
        let d = 15, h = false;
        if (hits.length > 0 && hits[0].distance < 15) { d = hits[0].distance; h = true; line.material = mH; line.scale.z = d/15; }
        else { line.material = mS; line.scale.z = 1; }
        pAll.push({ angle: ray.yaw, distance: d });
        if (!sq[ray.yaw] || d < sq[ray.yaw]) sq[ray.yaw] = d;
    });
    // Stats Update
    let crowd = 0; pAll.forEach(p => { if (p.distance < 12) crowd += (12 - p.distance); });
    let norm = Math.min(crowd / 150, 1);
    pH += (7.7 + norm*0.8 - pH) * 0.1; temp += (baseTemp + norm*15 - temp) * 0.1; moist += (1.0 + norm*2 - moist) * 0.1;
    document.getElementById('envData').innerHTML = `pH: ${pH.toFixed(2)}\nSıcaklık: ${temp.toFixed(1)}°C\nNem: ${moist.toFixed(1)}%`;
    
    const pAI = Object.keys(sq).map(y => ({ angle: parseFloat(y), distance: sq[y] }));
    if (ws && ws.readyState === 1 && clock.elapsedTime - lastS > 0.1) { ws.send(JSON.stringify({ lidar: pAI })); lastS = clock.elapsedTime; }
}

function animate() {
    requestAnimationFrame(animate); 
    const dt = clock.getDelta();
    updateCycle(dt); updatePhysics(dt); processSensors(dt);
    wheels.forEach(w => w.rotation.x -= throttle * 10 * dt);
    antenna.rotation.y += 2 * dt;
    updateCamera(); renderer.render(scene, camera);
}
animate();
window.addEventListener('resize', () => { camera.aspect = window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
