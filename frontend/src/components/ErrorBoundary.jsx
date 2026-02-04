import React from "react";

/**
 * Error Boundary to catch React rendering errors
 * Particularly useful for Portal-related DOM manipulation errors
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Check if it's a portal/DOM manipulation error we can safely ignore
    const errorMessage = error?.message || '';
    const isPortalError = 
      errorMessage.includes('removeChild') ||
      errorMessage.includes('insertBefore') ||
      errorMessage.includes('The node to be removed is not a child') ||
      errorMessage.includes('commitDeletion');

    if (isPortalError) {
      console.debug('[ErrorBoundary] Caught portal error:', errorMessage);
      // Don't set error state for portal errors - they're recoverable
      return { hasError: false, error: null };
    }

    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    const errorMessage = error?.message || '';
    const isPortalError = 
      errorMessage.includes('removeChild') ||
      errorMessage.includes('insertBefore') ||
      errorMessage.includes('The node to be removed is not a child');

    if (!isPortalError) {
      console.error('[ErrorBoundary] Uncaught error:', error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI for non-portal errors
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">Une erreur est survenue</h2>
            <p className="text-slate-600 mb-4">Nous nous excusons pour ce désagrément.</p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.href = '/';
              }}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Retour à l&apos;accueil
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
