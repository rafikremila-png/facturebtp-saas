import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// ============================================================
// RADIX UI / PORTAL FIX: Prevents "removeChild" errors
// These errors occur when navigating while portaled components
// (Select, Dialog, Popover) are open or animating.
// ============================================================

// 1. ResizeObserver error suppression (Radix UI triggers rapid callbacks)
if (typeof window !== 'undefined') {
  const OriginalResizeObserver = window.ResizeObserver;
  window.ResizeObserver = class ResizeObserver extends OriginalResizeObserver {
    constructor(callback) {
      super((entries, observer) => {
        window.requestAnimationFrame(() => {
          try {
            callback(entries, observer);
          } catch (e) {
            // Silently ignore ResizeObserver callback errors
          }
        });
      });
    }
  };
}

// 2. Patch removeChild to handle already-removed nodes gracefully
// This prevents "Failed to execute 'removeChild' on 'Node'" errors
if (typeof Node !== 'undefined') {
  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function(child) {
    if (child && child.parentNode !== this) {
      // Child already removed or parent changed - return silently
      console.debug('[Portal Fix] Prevented removeChild error - node already detached');
      return child;
    }
    return originalRemoveChild.call(this, child);
  };

  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function(newNode, referenceNode) {
    if (referenceNode && referenceNode.parentNode !== this) {
      // Reference node not in this parent - append instead
      console.debug('[Portal Fix] Prevented insertBefore error - reference node detached');
      return this.appendChild(newNode);
    }
    return originalInsertBefore.call(this, newNode, referenceNode);
  };
}

// 3. Global error handler for uncaught React portal errors
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    if (event.message && (
      event.message.includes('removeChild') ||
      event.message.includes('insertBefore') ||
      event.message.includes('The node to be removed is not a child')
    )) {
      console.debug('[Portal Fix] Suppressed DOM manipulation error:', event.message);
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
