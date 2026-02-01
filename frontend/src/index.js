import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress ResizeObserver loop error (common with Radix UI dropdowns)
// This error is benign and doesn't affect functionality
const resizeObserverErr = window.onerror;
window.onerror = (message, source, lineno, colno, error) => {
  if (message && message.toString().includes('ResizeObserver loop')) {
    return true;
  }
  if (resizeObserverErr) {
    return resizeObserverErr(message, source, lineno, colno, error);
  }
  return false;
};

// Also suppress in error event
window.addEventListener('error', (e) => {
  if (e.message && e.message.includes('ResizeObserver loop')) {
    e.stopPropagation();
    e.preventDefault();
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
