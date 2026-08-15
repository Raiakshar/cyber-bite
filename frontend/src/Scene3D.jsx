import { Component, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Grid, Icosahedron, Stars } from '@react-three/drei'
import * as THREE from 'three'

class SceneBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    if (this.state.failed) return null
    return this.props.children
  }
}

function ParticleField({ count = 700 }) {
  const ref = useRef()
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3)
    for (let i = 0; i < count * 3; i += 3) {
      arr[i] = (Math.random() - 0.5) * 24
      arr[i + 1] = (Math.random() - 0.5) * 14
      arr[i + 2] = -6 + Math.random() * 10
    }
    return arr
  }, [count])

  useFrame((_, delta) => {
    ref.current.rotation.y += delta * 0.02
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#00ff41"
        transparent
        opacity={0.85}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

function CoreShield() {
  const outer = useRef()
  const inner = useRef()
  const glow = useRef()

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime
    outer.current.rotation.x += delta * 0.12
    outer.current.rotation.y += delta * 0.2
    inner.current.rotation.x -= delta * 0.08
    inner.current.rotation.y += delta * 0.15
    glow.current.rotation.z += delta * 0.3
  })

  return (
    <Float speed={1.4} rotationIntensity={0.5} floatIntensity={0.8}>
      <group position={[0, 0, -4]}>
        <Icosahedron ref={outer} args={[2.1, 1]}>
          <meshBasicMaterial color="#00ff41" wireframe transparent opacity={0.28} />
        </Icosahedron>
        <Icosahedron ref={inner} args={[1.4, 1]}>
          <meshBasicMaterial color="#4dff88" wireframe transparent opacity={0.45} />
        </Icosahedron>
        <mesh ref={glow}>
          <sphereGeometry args={[0.55, 24, 24]} />
          <meshBasicMaterial color="#00ff41" transparent opacity={0.22} blending={THREE.AdditiveBlending} />
        </mesh>
      </group>
    </Float>
  )
}

function FloatingBits() {
  const bits = useMemo(() => {
    const arr = []
    for (let i = 0; i < 26; i++) {
      arr.push({
        position: [
          (Math.random() - 0.5) * 16,
          (Math.random() - 0.5) * 9,
          -3 - Math.random() * 6,
        ],
        scale: 0.05 + Math.random() * 0.12,
        speed: 0.4 + Math.random() * 0.8,
      })
    }
    return arr
  }, [])

  return (
    <group>
      {bits.map((b, i) => (
        <Float key={i} speed={b.speed} rotationIntensity={1.4} floatIntensity={2}>
          <mesh position={b.position} scale={b.scale}>
            <octahedronGeometry args={[1, 0]} />
            <meshBasicMaterial color={i % 2 ? '#00ff41' : '#4dff88'} wireframe transparent opacity={0.55} />
          </mesh>
        </Float>
      ))}
    </group>
  )
}

function Rig() {
  useFrame((state) => {
    const t = state.clock.elapsedTime
    state.camera.position.x = Math.sin(t * 0.1) * 0.7
    state.camera.position.y = 0.4 + Math.sin(t * 0.14) * 0.3
    state.camera.lookAt(0, 0, -3)
  })
  return null
}

export default function Scene3D() {
  return (
    <SceneBoundary>
      <div className="scene3d" aria-hidden="true">
        <Canvas
          dpr={[1, 1.5]}
          camera={{ position: [0, 0.4, 8], fov: 60 }}
          gl={{ antialias: true, alpha: true }}
          fallback={<div className="scene3d-fallback" />}
        >
          <color attach="background" args={['#020a04']} />
          <fog attach="fog" args={['#020a04', 9, 22]} />
          <ambientLight intensity={0.5} />
          <pointLight position={[6, 6, 6]} intensity={0.9} color="#00ff41" />
          <Stars radius={60} depth={40} count={1600} factor={3} saturation={0} fade speed={0.6} />
          <ParticleField count={700} />
          <CoreShield />
          <FloatingBits />
          <Grid
            position={[0, -3.4, 0]}
            cellSize={0.65}
            cellThickness={0.6}
            cellColor="#0a5c2c"
            sectionSize={3.25}
            sectionThickness={1.2}
            sectionColor="#00ff41"
            fadeDistance={30}
            fadeStrength={1.6}
            infiniteGrid
          />
          <Rig />
        </Canvas>
      </div>
    </SceneBoundary>
  )
}
