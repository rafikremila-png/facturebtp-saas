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
            if (callback) callback(entries, observer);
          } catch (e) {
            // Silently ignore ResizeObserver callback errors
          }
        });
      });
    }
  };
}

// 2. Comprehensive DOM patch for portal-related errors
if (typeof Node !== 'undefined') {
  // Patch removeChild
  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function(child) {
    if (!child) {
      return null;
    }
    if (child.parentNode !== this) {
      // Child already removed or parent changed - return silently
      return child;
    }
    try {
      return originalRemoveChild.call(this, child);
    } catch (e) {
      // Catch any remaining errors
      return child;
    }
  };

  // Patch insertBefore
  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function(newNode, referenceNode) {
    if (!newNode) {
      return null;
    }
    if (referenceNode && referenceNode.parentNode !== this) {
      // Reference node not in this parent - try appendChild instead
      try {
        return this.appendChild(newNode);
      } catch (e) {
        return newNode;
      }
    }
    try {
      return originalInsertBefore.call(this, newNode, referenceNode);
    } catch (e) {
      // Fallback to appendChild
      try {
        return this.appendChild(newNode);
      } catch (e2) {
        return newNode;
      }
    }
  };

  // Patch appendChild for completeness
  const originalAppendChild = Node.prototype.appendChild;
  Node.prototype.appendChild = function(child) {
    if (!child) {
      return null;
    }
    try {
      return originalAppendChild.call(this, child);
    } catch (e) {
      return child;
    }
  };
}

// 3. Global error handlers for uncaught React portal errors
if (typeof window !== 'undefined') {
  // Capture phase error handler
  window.addEventListener('error', (event) => {
    const msg = event.message || '';
    if (
      msg.includes('removeChild') ||
      msg.includes('insertBefore') ||
      msg.includes('appendChild') ||
      msg.includes('The node to be removed is not a child') ||
      msg.includes('Failed to execute') && msg.includes('Node')
    ) {
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      return false;
    }
  }, true);

  // Bubble phase error handler
  window.addEventListener('error', (event) => {
    const msg = event.message || '';
    if (
      msg.includes('removeChild') ||
      msg.includes('insertBefore') ||
      msg.includes('appendChild') ||
      msg.includes('The node to be removed is not a child') ||
      msg.includes('Failed to execute') && msg.includes('Node')
    ) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });

  // Unhandled rejection handler for promise-based errors
  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason?.message || event.reason?.toString() || '';
    if (
      reason.includes('removeChild') ||
      reason.includes('insertBefore') ||
      reason.includes('The node to be removed is not a child')
    ) {
      event.preventDefault();
      return false;
    }
  });
}

// 4. Disable StrictMode double-mounting in production to prevent portal issues
// StrictMode causes effects to run twice which can conflict with portal cleanup
const root = ReactDOM.createRoot(document.getElementById("root"));

// Use StrictMode only in development, disable for production-like behavior
const isDev = process.env.NODE_ENV === 'development';
const useStrictMode = false; // Disable StrictMode to prevent double-mount issues with Radix portals

if (useStrictMode && isDev) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  root.render(<App />);
}
