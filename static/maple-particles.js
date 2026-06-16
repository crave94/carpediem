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

  // Maple leaf SVG paths (unified with the Carpediem brand leaf)
  const LEAF_SVGS = [
    // Brand stylized maple leaf
    `<svg viewBox="0 0 32 32" fill="currentColor" width="16" height="16" aria-hidden="true">
      <path d="M16 3l2.5 5.5 6-1.5-2 5.5 4.5.5-5 3.5 1.5 6-5-3-2.5 6-2.5-6-5 3 1.5-6-5-.5 4.5-.5-2-5.5 6 1.5z"/>
    </svg>`,
    // Medium brand leaf
    `<svg viewBox="0 0 32 32" fill="currentColor" width="12" height="12" aria-hidden="true">
      <path d="M16 3l2.5 5.5 6-1.5-2 5.5 4.5.5-5 3.5 1.5 6-5-3-2.5 6-2.5-6-5 3 1.5-6-5-.5 4.5-.5-2-5.5 6 1.5z" opacity="0.85"/>
    </svg>`,
    // Small brand leaf
    `<svg viewBox="0 0 32 32" fill="currentColor" width="9" height="9" aria-hidden="true">
      <path d="M16 3l2.5 5.5 6-1.5-2 5.5 4.5.5-5 3.5 1.5 6-5-3-2.5 6-2.5-6-5 3 1.5-6-5-.5 4.5-.5-2-5.5 6 1.5z" opacity="0.7"/>
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
    const finalRotation = rotation * rotationDir;

    // Use direct inline properties for maximum mobile browser support
    leaf.style.cssText = `
      width: ${size}px;
      height: ${size}px;
      color: ${color};
      opacity: ${opacity};
      left: ${startLeft}%;
      animation: leaf-fall ${duration}s linear ${delay}s infinite;
      --leaf-drift: ${drift}px;
      --leaf-rotation: ${finalRotation}deg;
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