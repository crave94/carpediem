/**
 * EXP Animation Utilities
 * Floating EXP numbers, level-up bursts, etc.
 */
(function() {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) {
    window.MapleExpAnimations = { triggerLevelUp: () => {}, popExp: () => {} };
    return;
  }

  /**
   * Trigger level-up burst animation at screen center (or specific position)
   * @param {number} x - X position (optional, defaults to center)
   * @param {number} y - Y position (optional, defaults to center)
   */
  function triggerLevelUp(x, y) {
    const burst = document.createElement('div');
    burst.className = 'level-up-burst';

    const centerX = x ?? window.innerWidth / 2;
    const centerY = y ?? window.innerHeight / 2;

    burst.style.cssText = `left: ${centerX}px; top: ${centerY}px;`;

    // Create 3 expanding rings
    for (let i = 0; i < 3; i++) {
      const ring = document.createElement('div');
      ring.className = 'level-up-burst__ring';
      ring.style.cssText = `left: 0; top: 0;`;
      burst.appendChild(ring);
    }

    document.body.appendChild(burst);

    // Clean up after animation
    setTimeout(() => burst.remove(), 1000);
  }

  /**
   * Pop a floating EXP number at position
   * @param {string|number} amount - EXP amount to display
   * @param {number} x - X position
   * @param {number} y - Y position
   */
  function popExp(amount, x, y) {
    const el = document.createElement('div');
    el.className = 'maple-exp-pop';
    el.textContent = `+${typeof amount === 'number' ? amount.toLocaleString('es-ES') : amount}`;
    el.style.cssText = `left: ${x}px; top: ${y}px;`;

    document.body.appendChild(el);

    // Clean up after animation
    setTimeout(() => el.remove(), 1200);
  }

  /**
   * Check if a character just leveled up (compare previous level)
   * Call this after fetching character data
   * @param {Object} char - Character data with level
   * @param {number} prevLevel - Previous known level
   */
  function checkLevelUp(char, prevLevel) {
    if (char.level > prevLevel) {
      triggerLevelUp();
      // Could also pop EXP gained
      return true;
    }
    return false;
  }

  // Expose API
  window.MapleExpAnimations = {
    triggerLevelUp,
    popExp,
    checkLevelUp
  };
})();