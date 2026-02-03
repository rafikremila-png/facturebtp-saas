import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Disable React Error Overlay for ResizeObserver errors
// Must be done before React renders
if (typeof window !== 'undefined') {
  // Store original error handler
  const originalOnError = window.onerror;
  
  // Override window.onerror to suppress ResizeObserver errors
  window.onerror = function(message, source, lineno, colno, error) {
    if (message && message.toString().includes('ResizeObserver')) {
      return true; // Prevent default handling
    }
    if (originalOnError) {
      return originalOnError.call(this, message, source, lineno, colno, error);
    }
    return false;
  };

  // Suppress in error event
  window.addEventListener('error', (e) => {
    if (e.message && e.message.includes('ResizeObserver')) {
      e.stopImmediatePropagation();
      e.preventDefault();
    }
  }, true);

  // Suppress console.error for ResizeObserver
  const originalConsoleError = console.error;
  console.error = function(...args) {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
      return;
    }
    if (args[0] && args[0] instanceof Error && args[0].message && args[0].message.includes('ResizeObserver')) {
      return;
    }
    return originalConsoleError.apply(console, args);
  };

  // Patch the error overlay handler if it exists (webpack dev server)
  if (window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__) {
    const originalHook = window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__;
    window.__REACT_ERROR_OVERLAY_GLOBAL_HOOK__ = {
      ...originalHook,
      handleRuntimeError: (error) => {
        if (error && error.message && error.message.includes('ResizeObserver')) {
          return; // Skip ResizeObserver errors
        }
        if (originalHook.handleRuntimeError) {
          originalHook.handleRuntimeError(error);
        }
      }
    };
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
