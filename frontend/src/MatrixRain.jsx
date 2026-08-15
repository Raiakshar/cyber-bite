import { useEffect, useRef } from 'react'

const GLYPHS = (
  'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨ' +
  '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$#@%&*+=<>[]{}/\\|;:.'
)
const BODY = ['#00ff41', '#00e639', '#4dff88']

export default function MatrixRain({ className = '', opacity = 0.85 }) {
  const ref = useRef(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const ctx = canvas.getContext('2d')
    const FAR = 13
    const NEAR = 20
    let farDrops = []
    let nearDrops = []
    let raf = 0

    const setup = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = window.innerWidth * dpr
      canvas.height = window.innerHeight * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const farCols = Math.ceil(window.innerWidth / FAR)
      const nearCols = Math.ceil(window.innerWidth / NEAR)
      farDrops = Array.from({ length: farCols }, () => Math.floor(Math.random() * (window.innerHeight / FAR)))
      nearDrops = Array.from({ length: nearCols }, () => Math.floor(Math.random() * (window.innerHeight / NEAR)))
      ctx.fillStyle = '#020a04'
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight)
    }

    const glyph = () => GLYPHS[(Math.random() * GLYPHS.length) | 0]

    const drawPlane = (drops, size, bright) => {
      ctx.font = `${size}px "SF Mono", Menlo, Consolas, monospace`
      const limit = window.innerHeight
      for (let i = 0; i < drops.length; i++) {
        const x = i * size
        const y = drops[i] * size
        if (y < limit + size) {
          ctx.fillStyle = bright
          ctx.fillText(glyph(), x, y)
          ctx.fillStyle = BODY[i % BODY.length]
          ctx.fillText(glyph(), x, y + size)
        }
        if (y > limit + size || Math.random() < 0.004) drops[i] = 0
        else drops[i] = (y / size) + 1
      }
    }

    const tick = () => {
      ctx.fillStyle = 'rgba(2, 10, 4, 0.16)'
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight)
      drawPlane(farDrops, FAR, 'rgba(0, 255, 65, 0.32)')
      drawPlane(nearDrops, NEAR, '#c8ffd8')
      raf = requestAnimationFrame(tick)
    }

    setup()
    tick()
    window.addEventListener('resize', setup)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', setup)
    }
  }, [])

  return (
    <canvas
      ref={ref}
      className={`matrix-rain ${className}`}
      style={{ opacity }}
      aria-hidden="true"
    />
  )
}
