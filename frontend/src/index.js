import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Simple ResizeObserver error suppression
// This error is benign and occurs with Radix UI components
if (typeof window !== 'undefined') {
  const resizeObserverErr = window.ResizeObserver;
  window.ResizeObserver = class ResizeObserver extends resizeObserverErr {
    constructor(callback) {
      super((entries, observer) => {
        // Use requestAnimationFrame to batch observations
        window.requestAnimationFrame(() => {
          callback(entries, observer);
        });
      });
    }
  };
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
