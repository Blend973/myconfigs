// ==UserScript==
// @name         Universal Anti-Motion, GIF & Video Blocker First
// @namespace    Violentmonkey Scripts
// @version      4.0.0
// @description  Kills all animations, background canvases, control-less videos, and GIFs globally.
// @match        *://*/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const rules = `
        /* 1. Kill all CSS/JS motion globally (preserve interactive Canvas) */
        *:not(canvas, canvas *),
        *:not(canvas, canvas *)::before,
        *:not(canvas, canvas *)::after {
            animation: none !important;
            animation-duration: 0s !important;
            animation-iteration-count: 1 !important;
            transition: none !important;
            transition-duration: 0s !important;
            scroll-behavior: auto !important;
        }

        /* 2. Hide decorative background/overlay canvas animations (particles, fx) */
        canvas[class*="pointer-events-none"],
        canvas[class*="inset-0"] {
            display: none !important;
        }

        /* 3. Hide silent decorative videos and MP4 GIFs lacking user controls */
        video:not([controls]) {
            display: none !important;
        }

        /* 4. Suppress standard .gif image files */
        img[src*=".gif"],
        a[href*=".gif"] img {
            display: none !important;
        }
    `;

    function inject() {
        if (document.getElementById('universal-antimotion')) return;
        const style = document.createElement('style');
        style.id = 'universal-antimotion';
        style.textContent = rules;
        (document.head || document.documentElement).appendChild(style);
    }

    // Inject immediately at document-start
    if (document.documentElement) {
        inject();
    }

    // Keep active across dynamic page updates
    const observer = new MutationObserver(inject);
    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', inject);
    }
})();
