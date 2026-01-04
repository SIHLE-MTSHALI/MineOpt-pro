/**
 * ErrorBoundary.jsx - React Error Boundary Component
 * 
 * Catches JavaScript errors in child components and displays
 * a fallback UI instead of crashing the whole application.
 */

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({ errorInfo });
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    render() {
        if (this.state.hasError) {
            const { fallback, componentName } = this.props;

            // If a custom fallback is provided, use it
            if (fallback) {
                return fallback;
            }

            // Default fallback UI
            return (
                <div className="h-full flex items-center justify-center bg-slate-900">
                    <div className="text-center p-8 max-w-md">
                        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <AlertTriangle size={32} className="text-red-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-2">
                            {componentName || 'Component'} Failed to Load
                        </h3>
                        <p className="text-sm text-slate-400 mb-4">
                            An error occurred while rendering this component.
                            {this.state.error?.message?.includes('WebGL') && (
                                <span className="block mt-2 text-amber-400">
                                    WebGL may not be supported in your browser.
                                </span>
                            )}
                        </p>
                        <button
                            onClick={this.handleRetry}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                        >
                            <RefreshCw size={16} />
                            Try Again
                        </button>

                        {/* Error details for debugging */}
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <details className="mt-4 text-left text-xs text-slate-500">
                                <summary className="cursor-pointer hover:text-slate-400">
                                    Error Details
                                </summary>
                                <pre className="mt-2 p-2 bg-slate-800 rounded overflow-auto max-h-40">
                                    {this.state.error.toString()}
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </details>
                        )}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
