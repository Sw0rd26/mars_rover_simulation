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

// --- CELESTIAL BODIES (NIGHT SKY) ---
const skyGroup = new THREE.Group();
scene.add(skyGroup);

const starGeo = new THREE.BufferGeometry();
const starPos = [];
for(let i=0; i<800; i++) {
    const x = (Math.random() - 0.5) * 800;
    const y = Math.random() * 300 + 50; // Keep stars in upper hemisphere
    const z = (Math.random() - 0.5) * 800;
    starPos.push(x, y, z);
}
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
// fog: false perfectly allows the stars to pierce the thick Mars atmosphere!
const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, transparent: true, opacity: 0, fog: false });
const stars = new THREE.Points(starGeo, starMat);
skyGroup.add(stars);

// Phobos (Larger, faster moon)
const phobosGeo = new THREE.DodecahedronGeometry(12, 1);
const phobosMat = new THREE.MeshLambertMaterial({ color: 0xaaaaaa, emissive: 0x333333, transparent: true, opacity: 0, fog: false });
const phobos = new THREE.Mesh(phobosGeo, phobosMat);
phobos.position.set(-150, 120, -200);
skyGroup.add(phobos);

// Deimos (Smaller, slower moon)
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
    timeOfDay += dt; // The entire cycle is 90 seconds (45 Day, 45 Night)
    if (timeOfDay >= 90.0) timeOfDay = 0.0;
    
    // The state changes every 45.0 seconds
    let isNightPhase = (timeOfDay >= 45.0);
    
    if (isNightPhase) {
        targetColor.setHex(0x0a0f2b); // Midnight Blue
        targetIntensity = 0.15;       // Dim Night Light
        baseTemp = -73.0;             // Night Freezing Temp
    } else {
        targetColor.setHex(0x96321e); // Mars Red
        targetIntensity = 0.8;        // Bright Sun
        baseTemp = -40.0;             // Day Temp
    }
    
    // Smoothly interpolate the atmosphere and lighting for beautiful cinematic sunsets!
    scene.background.lerp(targetColor, 0.5 * dt);
    scene.fog.color.lerp(targetColor, 0.5 * dt);
    dirLight.intensity += (targetIntensity - dirLight.intensity) * 0.5 * dt;
    hemiLight.intensity = dirLight.intensity * 0.75; 
    
    // Fade in celestial cosmetics exclusively during Night phases
    let targetOpacity = isNightPhase ? 1.0 : 0.0;
    starMat.opacity += (targetOpacity - starMat.opacity) * 0.5 * dt;
    phobosMat.opacity = starMat.opacity;
    deimosMat.opacity = starMat.opacity;
    
    // Slowly orbit the moons around the celestial sphere
    phobos.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.05 * dt);
    deimos.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.02 * dt);
}

// --- MARS PROCEDURAL TERRAIN ---
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

// --- ROCKS ---
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

// --- BORDER WALL (CRATER RING) ---
const borderRadius = 120;
for (let a = 0; a < Math.PI * 2; a += 0.05) {
    const rock = new THREE.Mesh(rockGeo, rockMat);
    const rx = Math.sin(a) * borderRadius;
    const rz = Math.cos(a) * borderRadius;
    
    // Spawn massive towering mountain chunks to enclose the procedural simulation
    const scale = Math.random() * 5 + 10.0; 
    const ry = getGroundHeight(rx, rz);
    
    rock.position.set(rx, ry + scale * 0.4, rz);
    rock.scale.set(scale, scale * 2.0, scale); // Stretch height to create canyon walls!
    
    rock.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
    rock.castShadow = true;
    rock.receiveShadow = true;
    scene.add(rock);
    rocks.push(rock); // The AI's LiDAR automatically perceives these as legitimate obstacles!
}

// --- ROVER GEOMETRY ---
const rover = new THREE.Group();
rover.position.set(0, 5, 0);
scene.add(rover);

const bodyGeo = new THREE.BoxGeometry(1.8, 0.8, 2.5);
const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffd700 }); // Gold
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

const wheelOffsets = [
    [-1.2, 0.4, 1.3], [1.2, 0.4, 1.3],
    [-1.4, 0.4, 0], [1.4, 0.4, 0],
    [-1.2, 0.4, -1.3], [1.2, 0.4, -1.3]
];
for (let pos of wheelOffsets) {
    const w = new THREE.Mesh(wheelGeo, wheelMat);
    w.position.set(pos[0], pos[1], pos[2]);
    w.castShadow = true;
    rover.add(w);
    wheels.push(w);
}

// --- LIDAR SYSTEM ---
const raycaster = new THREE.Raycaster();
const lidarLines = new THREE.Group();
rover.add(lidarLines);
const lidarRange = 15.0;
const rays = []; // Now stores {yaw, pitch} for 3D Domed spheres

// Generate a 360-degree 3D Dome! (3 elevation rings, 36 rays each = 108 structural lasers)
const elevations = [0, 15, 30]; 
elevations.forEach(pitch => {
    for (let yaw = -170; yaw <= 180; yaw += 10) {
        rays.push({ yaw: yaw, pitch: pitch });
    }
});

const materialSafe = new THREE.LineBasicMaterial({ color: 0x00ff00 });
const materialHit = new THREE.LineBasicMaterial({ color: 0xff0000 });

rays.forEach(() => {
    const lg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, lidarRange)]);
    const line = new THREE.Line(lg, materialSafe);
    line.position.y = 0.5;
    lidarLines.add(line);
});

// --- STATE & INPUTS ---
let throttle = 0.0;
let steering = 0.0;
let manualThrottle = 0.0;
let manualSteering = 0.0;
let aiThrottle = 0.0;
let aiSteering = 0.0;
let override = false;
let autoSpeed = 6.0;
let autoTurnSpeed = 4.0;
let lastPayload = [];

// --- ENVIRONMENT STATS ---
let currentpH = 7.7;
let currentTemp = -40.0;
let currentMoisture = 1.0;

function updateEnvironmentStats(dt, payload) {
    if (payload.length === 0) return;
    
    // Calculate how 'crowded' the rover is by looking at all rocks within 12 meters
    let crowdedFactor = 0;
    payload.forEach(r => {
        if (r.distance < 12.0) {
            crowdedFactor += (12.0 - r.distance); 
        }
    });
    
    // Normalize the crowdedness purely dynamically
    let normalizedCrowd = Math.min(crowdedFactor / 150.0, 1.0); 
    
    // Calculate specific target ratios that naturally RISE when crowded
    let targetpH = 7.7 + (normalizedCrowd * 0.8);        // Min 7.7, Max 8.5
    let targetTemp = baseTemp + (normalizedCrowd * 15.0);// Base Temp dynamically drops to -73 at night and rises near rocks
    let targetMoisture = 1.0 + (normalizedCrowd * 2.0);  // Min 1.0%, Max 3.0%
    
    // Smoothly lerp towards target so they naturally "fall down" smoothly when rocks clear
    const smoothRate = 1.2 * dt; 
    currentpH += (targetpH - currentpH) * smoothRate;
    currentTemp += (targetTemp - currentTemp) * smoothRate;
    currentMoisture += (targetMoisture - currentMoisture) * smoothRate;
    
    const statsEl = document.getElementById('envData');
    if(statsEl) {
        statsEl.innerHTML = `pH Seviyesi : ${currentpH.toFixed(2)}\nSıcaklık    : ${currentTemp.toFixed(1)}°C\nNem Oranı   : ${currentMoisture.toFixed(1)}%`;
    }
}

document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') override = true;
    if (override) {
        if (e.code === 'KeyW') manualThrottle = 1.0;
        if (e.code === 'KeyS') manualThrottle = -1.0;
        if (e.code === 'KeyA') manualSteering = 1.0;
        if (e.code === 'KeyD') manualSteering = -1.0;
    }
});
document.addEventListener('keyup', (e) => {
    if (e.code === 'Space') { override = false; manualThrottle = 0; manualSteering = 0; }
    if (override) {
        if (e.code === 'KeyW' || e.code === 'KeyS') manualThrottle = 0;
        if (e.code === 'KeyA' || e.code === 'KeyD') manualSteering = 0;
    }
});

// --- WEBSOCKET CONNECTION ---
let ws;
function connectWS() {
    // Automatically switch to the Cloud AI Server if deployed to the real internet!
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const wsUrl = isLocal 
        ? 'ws://localhost:8000/ws' 
        : 'wss://mars-rover-simulation.onrender.com/ws'; 
        
    ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        aiThrottle = data.throttle;
        aiSteering = -data.steering;
    };
    ws.onopen = () => console.log('Edge AI Connected!');
    ws.onclose = () => { setTimeout(connectWS, 1000); };
}
connectWS();

const clock = new THREE.Clock();

function updateCamera() {
    const idealOffset = new THREE.Vector3(0, 10, -15);
    idealOffset.applyQuaternion(rover.quaternion);
    idealOffset.add(rover.position);
    camera.position.lerp(idealOffset, 0.1);

    const idealLook = new THREE.Vector3(0, 2, 5);
    idealLook.applyQuaternion(rover.quaternion);
    idealLook.add(rover.position);
    camera.lookAt(idealLook);
    
    // Snap skybox perfectly perfectly to the camera translation to create infinite horizon parallax depth!
    skyGroup.position.copy(camera.position);
}

function updatePhysics(dt) {
    let assistActive = false;
    let rearBrake = false;

    // Advanced Driver Assistance System (ADAS) Logic
    if (override) {
        throttle = manualThrottle;
        steering = manualSteering;

        // ADAS: Forward Collision Avoidance
        // If user is holding 'W', but the AI Edge node has engaged its dodge protocol (throttle 0.0 + steering)
        if (throttle > 0 && aiThrottle === 0.0) {
            assistActive = true;
            throttle = 0.0; // Emergency Brake
            steering = aiSteering; // Force AI Dodge vector
        }

        // ADAS: Rear Collision Avoidance (Parking Sensors)
        if (throttle < 0 && lastPayload.length > 0) {
            let closestRear = 15.0;
            rays.forEach((ray, i) => {
                if (Math.abs(ray.yaw) >= 135) {
                    closestRear = Math.min(closestRear, lastPayload[i].distance);
                }
            });
            if (closestRear < 5.5) {
                rearBrake = true;
                assistActive = true;
                throttle = 0.0; // Slam Brakes! Prevent backing up into the rock
                steering = manualSteering; // Let user steer to escape
            }
        }
    } else {
        throttle = aiThrottle;
        steering = aiSteering;
    }

    // Apply Steering
    rover.rotation.y += steering * autoTurnSpeed * dt;

    // Physical Collisions limits (Fallback if AI misses a corner)
    if (throttle !== 0) {
        let isBlocked = false;
        const sign = Math.sign(throttle);
        const rDir = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y).multiplyScalar(sign);

        const offsets = [
            new THREE.Vector3(0, 1.0, 0),
            new THREE.Vector3(1.2, 1.0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y),
            new THREE.Vector3(-1.2, 1.0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y)
        ];

        for (let off of offsets) {
            const origin = rover.position.clone().add(off);
            const hitTest = new THREE.Raycaster(origin, rDir);
            const hits = hitTest.intersectObjects(rocks);
            if (hits.length > 0 && hits[0].distance < 3.0) {
                isBlocked = true;
                break;
            }
        }

        if (!isBlocked) {
            const moveDist = throttle * autoSpeed * dt;
            const forward = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), rover.rotation.y);
            rover.position.addScaledVector(forward, moveDist);
        }
    }

    // Snap to procedural ground
    const groundY = getGroundHeight(rover.position.x, rover.position.z);
    rover.position.y = groundY;

    // Pitch calculation 
    const fwdY = getGroundHeight(rover.position.x + Math.sin(rover.rotation.y) * 2, rover.position.z + Math.cos(rover.rotation.y) * 2);
    const bwdY = getGroundHeight(rover.position.x - Math.sin(rover.rotation.y) * 2, rover.position.z - Math.cos(rover.rotation.y) * 2);
    rover.rotation.x = Math.atan2(bwdY - fwdY, 4.0);

    // Update Dashboard UI Strings
    let state = ws && ws.readyState === WebSocket.OPEN ? "Bağlandı" : "Bağlantı kesildi (Server'ı Başlat.";
    let hudText = `<h2>MARS ROVER SİSTEMİ</h2><p>Bağlantı: ${state}\nHareket: ${throttle.toFixed(2)}\nDönüş: ${(-steering).toFixed(2)}\nSürüş Sistemi: ${override ? 'Manuel (WASD)' : 'OTOPİLOT (Otonom Yapay Zeka)'}`;

    if (assistActive) {
        hudText += `<br><span style="color:#ff3333; font-weight:bold;">⚠️ KAZA ÖNLEYİCİ SİSTEM DEVREDE!</span>`;
        if (rearBrake) hudText += `<br><span style="color:#ffaa00;">Sistem aracın geriye doğru hareketini durdurdu.</span>`;
    }
    document.getElementById('hud').innerHTML = hudText + `</p>`;
}

let lastSend = 0;
function processSensorsAndNetwork(dt) {
    const payloadAll = []; // Full 108-ray buffer for local physics/ADAS
    const payloadAI = [];  // Filtered 36-ray packet for the remote AI
    const origin = new THREE.Vector3();
    rover.getWorldPosition(origin);
    origin.y += 0.5;

    rays.forEach((ray, i) => {
        const line = lidarLines.children[i];

        const yawRad = THREE.MathUtils.degToRad(ray.yaw);
        const pitchRad = THREE.MathUtils.degToRad(ray.pitch);

        // Compute 3D forward vector
        const localDir = new THREE.Vector3(
            Math.sin(yawRad) * Math.cos(pitchRad),
            Math.sin(pitchRad),
            Math.cos(yawRad) * Math.cos(pitchRad)
        ).normalize();

        const worldDir = localDir.applyQuaternion(rover.quaternion);
        raycaster.set(origin, worldDir);
        const intersects = raycaster.intersectObjects(rocks);

        line.rotation.y = yawRad; 
        line.rotation.x = -pitchRad; 

        let dist = lidarRange;
        let hit = false;
        if (intersects.length > 0 && intersects[0].distance < lidarRange) {
            dist = intersects[0].distance;
            hit = true;
            line.material = materialHit;
            line.scale.z = dist / lidarRange;
        } else {
            line.material = materialSafe;
            line.scale.z = 1.0;
        }

        const dataNode = { angle: ray.yaw, distance: dist, hit: hit, pitch: ray.pitch };
        payloadAll.push(dataNode);
        if (ray.pitch === 0) payloadAI.push(dataNode);
    });

    lastPayload = payloadAll; // Local physics now uses the FULL 108-ray set correctly!
    
    // Update geology dashboard dynamically
    updateEnvironmentStats(dt, payloadAll);

    if (ws && ws.readyState === WebSocket.OPEN) {
        if (clock.elapsedTime - lastSend > 0.1) { // Optimized 10Hz for cloud stability
            ws.send(JSON.stringify({ lidar: payloadAI }));
            lastSend = clock.elapsedTime;
        }
    }
}

// MAIN LOOP
function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();

    updateDayNightCycle(dt);
    updatePhysics(dt);
    processSensorsAndNetwork(dt);

    wheels.forEach(w => w.rotation.x -= throttle * 10 * dt);
    antenna.rotation.y += 2 * dt;

    updateCamera();
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
