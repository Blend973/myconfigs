// ==UserScript==
// @name         Universal Anti-Motion, GIF & Video Blocker
// @namespace    Violentmonkey Scripts
// @version      4.1.0
// @description  Kills all animations, freezes background canvases, control-less videos, and GIFs globally instead of hiding them.
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
    `;

    function inject() {
        if (!document.getElementById('universal-antimotion')) {
            const style = document.createElement('style');
            style.id = 'universal-antimotion';
            style.textContent = rules;
            (document.head || document.documentElement).appendChild(style);
        }
        processMedia();
    }

    function processMedia() {
        // Freeze control-less videos instead of hiding them
        document.querySelectorAll('video:not([controls])').forEach(video => {
            if (!video.paused) {
                video.pause();
            }
            if (!video._freezeHandler) {
                video._freezeHandler = true;
                video.addEventListener('play', () => video.pause(), true);
            }
        });

        // Freeze GIFs by capturing their first frame onto a static canvas
        document.querySelectorAll('img[src*=".gif"], a[href*=".gif"] img').forEach(img => {
            freezeGif(img);
        });
    }

    function freezeGif(img) {
        if (img.dataset.frozen) return;
        if (!img.complete) {
            img.addEventListener('load', () => freezeGif(img), { once: true });
            return;
        }
        try {
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width || 100;
            canvas.height = img.naturalHeight || img.height || 100;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            // Copy attributes and styles over to the static canvas
            for (let i = 0; i < img.attributes.length; i++) {
                const attr = img.attributes[i];
                if (attr.name !== 'src') {
                    canvas.setAttribute(attr.name, attr.value);
                }
            }
            canvas.style.cssText = img.style.cssText;
            canvas.className = img.className;
            canvas.dataset.frozen = 'true';

            if (img.parentNode) {
                img.parentNode.replaceChild(canvas, img);
            }
        } catch (e) {
            // Handles cross-origin (CORS) tainted images safely by marking them processed
            img.dataset.frozen = 'error';
        }
    }

    // Inject immediately at document-start
    if (document.documentElement) {
        inject();
    }

    // Keep active across dynamic page updates
    const observer = new MutationObserver(() => {
        inject();
    });

    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', inject);
    }
})();
