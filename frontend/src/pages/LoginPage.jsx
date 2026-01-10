import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const LoginPage = ({ onLogin, defaultMode = 'login' }) => {
    const navigate = useNavigate();
    const [isLogin, setIsLogin] = useState(defaultMode === 'login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('http://localhost:8000/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!response.ok) throw new Error('Invalid username or password');

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            onLogin(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccessMsg('');

        try {
            const response = await fetch('http://localhost:8000/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, email })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Registration failed');
            }

            setSuccessMsg('Account created! Please log in.');
            setIsLogin(true);
            setPassword('');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDemoLogin = async () => {
        setLoading(true);
        setError('');

        try {
            const formData = new URLSearchParams();
            formData.append('username', 'admin');
            formData.append('password', 'admin');

            const response = await fetch('http://localhost:8000/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Demo login failed - ensure backend is running');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            onLogin(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Inline styles for reliable rendering
    const styles = {
        container: {
            minHeight: '100vh',
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
            padding: '24px',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        },
        card: {
            width: '100%',
            maxWidth: '420px',
            background: 'rgba(30, 41, 59, 0.95)',
            borderRadius: '16px',
            padding: '40px 32px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            border: '1px solid rgba(71, 85, 105, 0.5)'
        },
        logo: {
            width: '64px',
            height: '64px',
            background: 'linear-gradient(135deg, #3b82f6, #10b981)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 10px 40px rgba(59, 130, 246, 0.3)'
        },
        title: {
            fontSize: '28px',
            fontWeight: 700,
            color: '#ffffff',
            textAlign: 'center',
            marginBottom: '8px'
        },
        subtitle: {
            fontSize: '14px',
            color: '#94a3b8',
            textAlign: 'center',
            marginBottom: '32px'
        },
        errorBox: {
            padding: '12px 16px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#f87171',
            fontSize: '14px',
            marginBottom: '20px',
            textAlign: 'center'
        },
        successBox: {
            padding: '12px 16px',
            background: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            borderRadius: '8px',
            color: '#4ade80',
            fontSize: '14px',
            marginBottom: '20px',
            textAlign: 'center'
        },
        formGroup: {
            marginBottom: '20px'
        },
        label: {
            display: 'block',
            fontSize: '14px',
            fontWeight: 500,
            color: '#e2e8f0',
            marginBottom: '8px'
        },
        input: {
            width: '100%',
            padding: '14px 16px',
            background: '#0f172a',
            border: '1px solid #334155',
            borderRadius: '10px',
            color: '#f1f5f9',
            fontSize: '16px',
            outline: 'none',
            transition: 'border-color 0.2s, box-shadow 0.2s',
            boxSizing: 'border-box'
        },
        primaryButton: {
            width: '100%',
            padding: '14px',
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            border: 'none',
            borderRadius: '10px',
            color: '#ffffff',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'transform 0.2s, box-shadow 0.2s',
            boxShadow: '0 4px 20px rgba(59, 130, 246, 0.3)'
        },
        secondaryButton: {
            width: '100%',
            padding: '12px',
            background: 'transparent',
            border: '1px solid #475569',
            borderRadius: '10px',
            color: '#94a3b8',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.2s',
            marginTop: '12px'
        },
        divider: {
            display: 'flex',
            alignItems: 'center',
            margin: '24px 0',
            gap: '16px'
        },
        dividerLine: {
            flex: 1,
            height: '1px',
            background: '#334155'
        },
        dividerText: {
            fontSize: '12px',
            color: '#64748b',
            textTransform: 'uppercase'
        },
        toggleLink: {
            display: 'block',
            textAlign: 'center',
            marginTop: '24px',
            color: '#94a3b8',
            fontSize: '14px',
            cursor: 'pointer'
        },
        backLink: {
            display: 'block',
            textAlign: 'center',
            marginTop: '16px',
            color: '#64748b',
            fontSize: '13px',
            textDecoration: 'none'
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                {/* Logo */}
                <div style={styles.logo}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                </div>

                {/* Title */}
                <h1 style={styles.title}>MineOpt Pro</h1>
                <p style={styles.subtitle}>
                    {isLogin ? 'Sign in to your account' : 'Create your account'}
                </p>

                {/* Error/Success Messages */}
                {error && <div style={styles.errorBox}>{error}</div>}
                {successMsg && <div style={styles.successBox}>{successMsg}</div>}

                {/* Form */}
                <form onSubmit={isLogin ? handleLogin : handleRegister}>
                    <div style={styles.formGroup}>
                        <label style={styles.label}>Username</label>
                        <input
                            type="text"
                            required
                            placeholder="Enter your username"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            style={styles.input}
                        />
                    </div>

                    {!isLogin && (
                        <div style={styles.formGroup}>
                            <label style={styles.label}>Email (optional)</label>
                            <input
                                type="email"
                                placeholder="you@company.com"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                style={styles.input}
                            />
                        </div>
                    )}

                    <div style={styles.formGroup}>
                        <label style={styles.label}>Password</label>
                        <input
                            type="password"
                            required
                            placeholder="••••••••"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            style={styles.input}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            ...styles.primaryButton,
                            opacity: loading ? 0.7 : 1,
                            cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
                    </button>
                </form>

                {/* Divider */}
                <div style={styles.divider}>
                    <div style={styles.dividerLine}></div>
                    <span style={styles.dividerText}>or</span>
                    <div style={styles.dividerLine}></div>
                </div>

                {/* Demo Login */}
                <button
                    onClick={handleDemoLogin}
                    disabled={loading}
                    style={{
                        ...styles.secondaryButton,
                        marginTop: 0,
                        opacity: loading ? 0.7 : 1
                    }}
                >
                    🚀 Quick Demo Access (admin/admin)
                </button>

                {/* Toggle Login/Register */}
                <p
                    style={styles.toggleLink}
                    onClick={() => { setIsLogin(!isLogin); setError(''); setSuccessMsg(''); }}
                >
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <span style={{ color: '#3b82f6', fontWeight: 500 }}>
                        {isLogin ? 'Sign Up' : 'Sign In'}
                    </span>
                </p>

                {/* Back to Home */}
                <Link to="/" style={styles.backLink}>
                    ← Back to Home
                </Link>
            </div>
        </div>
    );
};

export default LoginPage;
