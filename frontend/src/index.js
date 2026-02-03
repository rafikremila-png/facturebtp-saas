import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress ResizeObserver "loop completed" error globally
// This error is benign and commonly occurs with Radix UI components
if (typeof window !== 'undefined') {
  const originalError = window.console.error;
  window.console.error = (...args) => {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
      return;
    }
    originalError.apply(console, args);
  };

  // Also suppress in error event listener
  window.addEventListener('error', (event) => {
    if (event.message && event.message.includes('ResizeObserver')) {
      event.stopImmediatePropagation();
      event.preventDefault();
      return false;
    }
  }, true);
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
