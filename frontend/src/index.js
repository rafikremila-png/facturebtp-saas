import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Patch ResizeObserver to prevent "loop completed" errors
// This is a known issue with Radix UI components
const RO = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends RO {
  constructor(callback) {
    super((entries, observer) => {
      // Use requestAnimationFrame to batch observations
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

// Suppress ResizeObserver error messages globally
const errorHandler = (event) => {
  if (event.message && event.message.includes('ResizeObserver')) {
    event.stopImmediatePropagation();
    event.preventDefault();
    return true;
  }
};

window.addEventListener('error', errorHandler, true);
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && event.reason.message.includes('ResizeObserver')) {
    event.preventDefault();
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
