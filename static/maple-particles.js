/**
 * Maple Leaf Particle System
 * Replaces generic twinkling stars with falling maple leaves
 * Respects prefers-reduced-motion
 */
(function() {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return;

  const leavesLayer = document.getElementById('leavesLayer');
  if (!leavesLayer) return;

  // Maple leaf SVG paths (optimized for small size)
  const LEAF_SVGS = [
    // Classic maple leaf
    `<svg viewBox="0 0 32 32" fill="currentColor" width="16" height="16" aria-hidden="true">
      <path d="M16 2C10.5 2 6 5.5 6 10c0 2.5 1.5 4.5 4 6.5 2.5 2 4.5 4.5 6 7 1.5-2.5 3.5-5 6-7 2.5-2 4-4 4-6.5C26 5.5 21.5 2 16 2z"/>
      <path d="M16 5.5c-2.2 0-4 1.8-4 4 0 1.1.7 2 1.5 3.5.8 1.5 1.8 3 2.5 4.5.7-1.5 1.7-3 2.5-4.5.8-1.5 1.5-2.4 1.5-3.5C20 7.3 18.2 5.5 16 5.5z" fill="rgba(255,255,255,0.3)"/>
    </svg>`,
    // Small maple leaf
    `<svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12" aria-hidden="true">
      <path d="M12 1C7.5 1 4 3.5 4 7c0 1.8 1.2 3.2 3 5 1.8 1.8 3.2 4 4 6.5 0.8-1.5 2-3 3-5 1-1.8 2.5-3.5 3-5.5C20 3.5 16.5 1 12 1z"/>
    </svg>`,
    // Leaf cluster
    `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" aria-hidden="true">
      <path d="M10 1C6 1 3 3 3 6c0 1.2.8 2.2 2 3.5 1 1 2 2 3 3.5 2-2.5 3-4 4-6 1-2 2-4 3-5C17 3 14 1 10 1z"/>
    </svg>`
  ];

  // Leaf colors (MapleStory palette)
  const LEAF_COLORS = [
    '#E53935',  // Warrior red
    '#A855F7',  // Mage purple
    '#3B82F6',  // Archer blue
    '#FB8C00',  // Thief orange
    '#00ACC1',  // Pirate cyan
    '#84CC16',  // Xenon green
    '#F472B6',  // Pink bean
    '#FFF'     // White
  ];

  // Configuration
  const CONFIG = {
    leafCount: Math.min(60, Math.floor(window.innerWidth * window.innerHeight / 20000)),
    minSize: 10,
    maxSize: 24,
    minDuration: 12,
    maxDuration: 22,
    minDelay: 0,
    maxDelay: 5,
    driftAmount: 40, // pixels of horizontal drift
    rotationRange: 360
  };

  function createLeaf(index) {
    const leaf = document.createElement('div');
    leaf.className = 'maple-leaf';
    leaf.setAttribute('aria-hidden', 'true');

    // Random properties
    const size = CONFIG.minSize + Math.random() * (CONFIG.maxSize - CONFIG.minSize);
    const color = LEAF_COLORS[Math.floor(Math.random() * LEAF_COLORS.length)];
    const svg = LEAF_SVGS[Math.floor(Math.random() * LEAF_SVGS.length)];
    const duration = CONFIG.minDuration + Math.random() * (CONFIG.maxDuration - CONFIG.minDuration);
    const delay = Math.random() * CONFIG.maxDelay;
    const drift = (Math.random() - 0.5) * 2 * CONFIG.driftAmount;
    const rotation = Math.random() * CONFIG.rotationRange;
    const rotationDir = Math.random() > 0.5 ? 1 : -1;
    const startLeft = Math.random() * 100;
    const opacity = 0.25 + Math.random() * 0.35;

    // Use CSS custom properties for animation
    leaf.style.cssText = `
      --leaf-size: ${size}px;
      --leaf-color: ${color};
      --leaf-duration: ${duration}s;
      --leaf-delay: ${delay}s;
      --leaf-drift: ${drift}px;
      --leaf-rotation: ${rotation}deg;
      --leaf-rotation-dir: ${rotationDir};
      --leaf-opacity: ${opacity};
      left: ${startLeft}%;
      animation: leaf-fall var(--leaf-duration) linear var(--leaf-delay) infinite;
    `;

    leaf.innerHTML = svg;

    return leaf;
  }

  // Initialize leaves
  function initLeaves() {
    // Clear any existing
    leavesLayer.innerHTML = '';

    // Create leaves in batches to avoid blocking
    const batchSize = 10;
    let created = 0;

    function createBatch() {
      const fragment = document.createDocumentFragment();
      const count = Math.min(batchSize, CONFIG.leafCount - created);

      for (let i = 0; i < count; i++) {
        fragment.appendChild(createLeaf(created + i));
      }

      leavesLayer.appendChild(fragment);
      created += count;

      if (created < CONFIG.leafCount) {
        requestAnimationFrame(createBatch);
      }
    }

    createBatch();
  }

  // Handle window resize - adjust leaf count
  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      CONFIG.leafCount = Math.min(60, Math.floor(window.innerWidth * window.innerHeight / 20000));
      initLeaves();
    }, 250);
  });

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLeaves);
  } else {
    initLeaves();
  }

  // Expose for debugging
  window.MapleParticles = { init: initLeaves, config: CONFIG };
})();