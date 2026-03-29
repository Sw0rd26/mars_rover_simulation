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

const phobosGeo = new THREE.DodecahedronGeometry(12, 1);
const phobosMat = new THREE.MeshLambertMaterial({ color: 0xaaaaaa, emissive: 0x333333, transparent: true, opacity: 0, fog: false });
const phobos = new THREE.Mesh(phobosGeo, phobosMat);
phobos.position.set(-150, 120, -200);
skyGroup.add(phobos);

const deimosGeo = new THREE.DodecahedronGeometry(6, 0);
const deimosMat = new THREE.MeshLambertMaterial({ color: 0x888888, emissive: 0x222222, transparent: true, opacity: 0, fog: false });
const deimos = new THREE.Mesh(deimosGeo, deimosMat);
deimos.position.set(180, 150, -150);
skyGroup.add(deimos);

// --- DAY / NIGHT CYCLE ---
let timeOfDay = 0.0;
let targetColor = new THREE.Color(0x96321e);
let targetIntensity = 0.8;
let baseTemp = -40.0;
function updateDayNightCycle(dt) {
    timeOfDay += dt;
    if (timeOfDay >= 90.0) timeOfDay = 0.0;
    let isNightPhase = (timeOfDay >= 45.0);
    if (isNightPhase) {
        targetColor.setHex(0x0a0f2b);
        targetIntensity = 0.15;
        baseTemp = -73.0;
    } else {
        targetColor.setHex(0x96321e);
        targetIntensity = 0.8;
        baseTemp = -40.0;
    }
    scene.background.lerp(targetColor, 0.5 * dt);
    scene.fog.color.lerp(targetColor, 0.5 * dt);
    dirLight.intensity += (targetIntensity - dirLight.intensity) * 0.5 * dt;
    hemiLight.intensity = dirLight.intensity * 0.75; 
    let targetOpacity = isNightPhase ? 1.0 : 0.0;
    starMat.opacity += (targetOpacity - starMat.opacity) * 0.5 * dt;
    phobosMat.opacity = starMat.opacity;
    deimosMat.opacity = starMat.opacity;
    phobos.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.05 * dt);
    deimos.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.02 * dt);
}

// --- TERRAIN ---
const terrainSize = 250;
const geometry = new THREE.PlaneGeometry(terrainSize, terrainSize, 64, 64);
geometry.rotateX(-Math.PI / 2);
function getGroundHeight(x, z) {
    let y = Math.sin(x / 10) * Math.cos(z / 10) * 2.5;
    y += Math.sin(x / 5 + z / 3) * 1.5;
    return y;
}
const posAttr = geometry.attributes.position;
for (let i = 0; i < posAttr.count; i++) {
    const x = posAttr.getX(i);
    const z = posAttr.getZ(i);
    posAttr.setY(i, getGroundHeight(x, z));
}
geometry.computeVertexNormals();
const groundMat = new THREE.MeshStandardMaterial({ color: 0xb45032, roughness: 0.9, flatShading: true });
const ground = new THREE.Mesh(geometry, groundMat);
ground.receiveShadow = true;
scene.add(ground);

const rocks = [];
const rockGeo = new THREE.DodecahedronGeometry(1, 0);
const rockMat = new THREE.MeshStandardMaterial({ color: 0x64281e, roughness: 1.0, flatShading: true, side: THREE.DoubleSide });
for (let i = 0; i < 100; i++) {
    const rock = new THREE.Mesh(rockGeo, rockMat);
    const rx = (Math.random() - 0.5) * 180;
    const rz = (Math.random() - 0.5) * 180;
    if (Math.abs(rx) < 15 && Math.abs(rz) < 15) continue;
    const scale = Math.random() * 2 + 1.5;
    const ry = getGroundHeight(rx, rz);
    rock.position.set(rx, ry + scale * 0.5, rz);
    rock.scale.set(scale, scale, scale);
    rock.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
    rock.castShadow = true;
    rock.receiveShadow = true;
    scene.add(rock);
    rocks.push(rock);
}

const borderRadius = 120;
for (let a = 0; a < Math.PI * 2; a += 0.05) {
    const rock = new THREE.Mesh(rockGeo, rockMat);
    const rx = Math.sin(a) * borderRadius;
    const rz = Math.cos(a) * borderRadius;
    const scale = Math.random() * 5 + 10.0; 
    const ry = getGroundHeight(rx, rz);
    rock.position.set(rx, ry + scale * 0.4, rz);
    rock.scale.set(scale, scale * 2.0, scale);
    rock.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
    rock.castShadow = true;
    rock.receiveShadow = true;
    scene.add(rock);
    rocks.push(rock);
}

// --- ROVER ---
const rover = new THREE.Group();
rover.position.set(0, 5, 0);
scene.add(rover);
const bodyGeo = new THREE.BoxGeometry(1.8, 0.8, 2.5);
const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffd700 });
const body = new THREE.Mesh(bodyGeo, bodyMat);
body.position.y = 1.0;
body.castShadow = true;
rover.add(body);
const antennaGeometry = new THREE.CylinderGeometry(0.05, 0.05, 1.5);
const antennaMat = new THREE.MeshStandardMaterial({ color: 0xaaaaaa });
const antenna = new THREE.Mesh(antennaGeometry, antennaMat);
antenna.position.set(-0.4, 1.8, -0.4);
rover.add(antenna);
const dishGeo = new THREE.SphereGeometry(0.3, 16, 16);
const dish = new THREE.Mesh(dishGeo, antennaMat);
dish.position.y = 0.75;
antenna.add(dish);
const wheels = [];
const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.4, 16);
wheelGeo.rotateZ(Math.PI / 2);
const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
const wheelOffsets = [[-1.2, 0.4, 1.3], [1.2, 0.4, 1.3], [-1.4, 0.4, 0], [1.4, 0.4, 0], [-1.2, 0.4, -1.3], [1.2, 0.4, -1.3]];
for (let pos of wheelOffsets) {
    const w = new THREE.Mesh(wheelGeo, wheelMat);
    w.position.set(pos[0], pos[1], pos[2]);
    w.castShadow = true;
    rover.add(w);
    wheels.push(w);
}

// --- 3D SPHERICAL LIDAR (HEDGEHOG MODE) ---
const raycaster = new THREE.Raycaster();
const lidarLines = new THREE.Group();
rover.add(lidarLines);
const lidarRange = 15.0;
const rays = [];
const elevations = [0, 15, 30]; 
elevations.forEach(pitch => {
    for (let yaw = -170; yaw <= 180; yaw += 10) { rays.push({ yaw: yaw, pitch: pitch }); }
});
const matSafe = new THREE.LineBasicMaterial({ color: 0x00ff00 }), matHit = new THREE.LineBasicMaterial({ color: 0xff0000 });
rays.forEach(() => {
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,lidarRange)]), matSafe);
    line.position.y = 0.5;
    lidarLines.add(line);
});

// --- INPUTS & AI STATE ---
let throttle = 0.0, steering = 0.0, manualThrottle = 0.0, manualSteering = 0.0, aiThrottle = 0.0, aiSteering = 0.0;
let override = false, autoSpeed = 4.0, autoTurnSpeed = 6.0;
let lastSend = 0;

function updateEnvironmentStats(dt, payloadAll) {
    if (payloadAll.length === 0) return;
    let crowded = 0;
    payloadAll.forEach(r => { if (r.distance < 12.0) crowded += (12.0 - r.distance); });
    let norm = Math.min(crowded / 150.0, 1.0); 
    const statsEl = document.getElementById('envData');
    if(statsEl) statsEl.innerHTML = `pH: ${(7.7 + norm*0.8).toFixed(2)} | Temp: ${(baseTemp + norm*15).toFixed(1)}°C | Humid: ${(1.0 + norm*2).toFixed(1)}%`;
}

document.addEventListener('keydown', e => {
    if (e.code === 'Space') override = true;
    if (override) {
        if (e.code === 'KeyW') manualThrottle = 1.0; if (e.code === 'KeyS') manualThrottle = -1.0;
        if (e.code === 'KeyA') manualSteering = 1.0; if (e.code === 'KeyD') manualSteering = -1.0;
    }
});
document.addEventListener('keyup', e => {
    if (e.code === 'Space') { override = false; manualThrottle = 0; manualSteering = 0; }
    if (override) {
        if (e.code === 'KeyW' || e.code === 'KeyS') manualThrottle = 0;
        if (e.code === 'KeyA' || e.code === 'KeyD') manualSteering = 0;
    }
});

let ws;
function connectWS() {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const wsUrl = isLocal ? 'ws://localhost:8000/ws' : 'wss://mars-rover-simulation.onrender.com/ws'; 
    ws = new WebSocket(wsUrl);
    ws.onmessage = e => { const d = JSON.parse(e.data); aiThrottle = d.throttle; aiSteering = -d.steering; };
    ws.onclose = () => setTimeout(connectWS, 1000);
}
connectWS();

const clock = new THREE.Clock();

function updateCamera() {
    // SNAPPY CLASSIC CAMERA (No Lerp Jitter)
    const pos = new THREE.Vector3(0, 8, -12).applyQuaternion(rover.quaternion).add(rover.position);
    camera.position.set(pos.x, pos.y, pos.z);
    const look = new THREE.Vector3(0, 2, 5).applyQuaternion(rover.quaternion).add(rover.position);
    camera.lookAt(look);
    skyGroup.position.copy(camera.position);
}

// --- GLIDE ADAS ---
function updatePhysics(dt) {
    let assist = false, brake = false;
    if (override) { throttle = manualThrottle; steering = manualSteering; } 
    else { throttle = aiThrottle; steering = aiSteering; }

    if (throttle !== 0 || steering !== 0) {
        let block = false, hazardF = false, hazardR = false;
        const sign = Math.sign(throttle) || 1.0;
        const rDir = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y).multiplyScalar(sign);
        const offs = [new THREE.Vector3(0, 0.8, 0), new THREE.Vector3(0.7, 0.8, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y), new THREE.Vector3(-0.7, 0.8, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y)];
        
        for (let off of offs) {
            const hitTest = new THREE.Raycaster(rover.position.clone().add(off), rDir);
            const hits = hitTest.intersectObjects(rocks);
            if (hits.length > 0) {
                const d = hits[0].distance;
                if (throttle > 0 && d < 8.0) hazardF = true;
                if (throttle < 0 && d < 2.5) hazardR = true;
                if (d < 1.0) { block = true; break; }
            }
        }

        if (hazardF) { assist = true; throttle *= 0.5; if (override) steering = aiSteering; }
        if (hazardR) { assist = true; brake = true; throttle = 0.0; }

        if (!block) {
            rover.rotation.y += steering * autoTurnSpeed * dt;
            const forward = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y);
            rover.position.addScaledVector(forward, throttle * autoSpeed * dt);
        }
    }

    rover.position.y = getGroundHeight(rover.position.x, rover.position.z);
    const fY = getGroundHeight(rover.position.x + Math.sin(rover.rotation.y)*2, rover.position.z + Math.cos(rover.rotation.y)*2);
    const bY = getGroundHeight(rover.position.x - Math.sin(rover.rotation.y)*2, rover.position.z - Math.cos(rover.rotation.y)*2);
    rover.rotation.x = Math.atan2(bY - fY, 4.0);

    let hud = `<h2>MARS ROVER</h2>Hız: ${throttle.toFixed(2)} | Dönüş: ${(-steering).toFixed(2)}\n${override ? 'MANUEL' : 'OTOPİLOT'}`;
    if (assist && override) hud += `<br><span style="color:#ff3333;">⚠️ ADAS AKTİF ${brake ? '(BRAK)' : '(DODGE)'}</span>`;
    document.getElementById('hud').innerHTML = hud;
}

function processSensorsAndNetwork(dt) {
    const pAll = [];
    const origin = rover.position.clone(); origin.y += 0.5;
    
    // VOLUMETRIC SQUASH: Map 3D Rings to a 2D AI Array
    const squash = {};

    rays.forEach((ray, i) => {
        const line = lidarLines.children[i];
        const yawR = THREE.MathUtils.degToRad(ray.yaw), pitchR = THREE.MathUtils.degToRad(ray.pitch);
        const lDir = new THREE.Vector3(Math.sin(yawR) * Math.cos(pitchR), Math.sin(pitchR), Math.cos(yawR) * Math.cos(pitchR)).normalize();
        const wDir = lDir.applyQuaternion(rover.quaternion);
        
        raycaster.set(origin, wDir);
        const hits = raycaster.intersectObjects(rocks);
        line.rotation.y = yawR; line.rotation.x = -pitchR; 
        
        let dist = lidarRange, hit = false;
        if (hits.length > 0 && hits[0].distance < lidarRange) {
            dist = hits[0].distance; hit = true;
            line.material = matHit; line.scale.z = dist / lidarRange;
        } else {
            line.material = matSafe; line.scale.z = 1.0;
        }
        
        pAll.push({ angle: ray.yaw, distance: dist, hit: hit, pitch: ray.pitch });
        
        // --- THE MAGIC BRIDGE: Squashing 108 rays into a 36-ray 2D cloud ---
        // For every yaw angle, the AI only cares about the ABSOLUTE CLOSEST rock (any height!)
        if (!squash[ray.yaw] || dist < squash[ray.yaw]) {
            squash[ray.yaw] = dist;
        }
    });

    const pAI = Object.keys(squash).map(yaw => ({ angle: parseFloat(yaw), distance: squash[yaw] }));

    updateEnvironmentStats(dt, pAll);
    if (ws && ws.readyState === WebSocket.OPEN && clock.elapsedTime - lastSend > 0.1) {
        ws.send(JSON.stringify({ lidar: pAI })); lastSend = clock.elapsedTime;
    }
}

function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();
    updateDayNightCycle(dt); updatePhysics(dt); processSensorsAndNetwork(dt);
    wheels.forEach(w => w.rotation.x -= throttle * 10 * dt);
    antenna.rotation.y += 2 * dt;
    updateCamera();
    renderer.render(scene, camera);
}
animate();
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
