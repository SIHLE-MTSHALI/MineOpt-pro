import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage = () => {
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const features = [
        {
            icon: '📅',
            title: 'Intelligent Scheduling',
            description: '8-stage optimization pipeline with fast and full pass modes. Schedule 14+ days of operations in seconds.'
        },
        {
            icon: '🧪',
            title: 'Quality Management',
            description: 'Blending optimization with ARB/ADB/DAF basis conversion. Meet product specs with penalty-aware decisions.'
        },
        {
            icon: '📦',
            title: 'Stockpile Tracking',
            description: 'FIFO, LIFO, and proportional reclaim. Staged stockpiles with state machine and quality targets.'
        },
        {
            icon: '🏭',
            title: 'Wash Plant Integration',
            description: 'Cutpoint optimization modes: Fixed RD, Target Quality, or Optimizer-selected for maximum value.'
        },
        {
            icon: '📊',
            title: 'Comprehensive Reporting',
            description: '9 standard report types with PDF, CSV, and JSON exports. Schedule automated report delivery.'
        },
        {
            icon: '🔐',
            title: 'Enterprise Security',
            description: 'Role-based access control with 18 granular permissions. Complete audit trail for compliance.'
        }
    ];

    const stats = [
        { value: '14+', label: 'Days Ahead Planning' },
        { value: '8', label: 'Optimization Stages' },
        { value: '9', label: 'Report Types' },
        { value: '100%', label: 'Quality Traceability' }
    ];

    const styles = {
        page: {
            minHeight: '100vh',
            background: '#0f172a',
            color: '#ffffff',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        },
        nav: {
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 100,
            padding: '16px 24px',
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(51, 65, 85, 0.5)'
        },
        navInner: {
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
        },
        logo: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        logoIcon: {
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #3b82f6, #10b981)',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '20px'
        },
        logoText: {
            fontSize: '20px',
            fontWeight: 700,
            color: '#ffffff'
        },
        navButtons: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        navButtonSecondary: {
            padding: '10px 20px',
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            fontSize: '15px',
            fontWeight: 500,
            cursor: 'pointer',
            borderRadius: '8px',
            transition: 'color 0.2s'
        },
        navButtonPrimary: {
            padding: '10px 24px',
            background: 'linear-gradient(135deg, #3b82f6, #10b981)',
            border: 'none',
            color: '#ffffff',
            fontSize: '15px',
            fontWeight: 600,
            cursor: 'pointer',
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(59, 130, 246, 0.3)'
        },
        hero: {
            paddingTop: '140px',
            paddingBottom: '80px',
            textAlign: 'center',
            maxWidth: '900px',
            margin: '0 auto',
            padding: '140px 24px 80px'
        },
        badge: {
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid #334155',
            borderRadius: '100px',
            marginBottom: '32px'
        },
        badgeDot: {
            width: '8px',
            height: '8px',
            background: '#10b981',
            borderRadius: '50%'
        },
        badgeText: {
            fontSize: '14px',
            color: '#94a3b8'
        },
        heading: {
            fontSize: 'clamp(36px, 6vw, 64px)',
            fontWeight: 700,
            lineHeight: 1.1,
            marginBottom: '24px',
            color: '#ffffff'
        },
        headingAccent: {
            background: 'linear-gradient(135deg, #3b82f6, #10b981)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
        },
        subheading: {
            fontSize: '18px',
            lineHeight: 1.7,
            color: '#94a3b8',
            maxWidth: '600px',
            margin: '0 auto 40px'
        },
        ctaButtons: {
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '16px',
            marginBottom: '64px'
        },
        ctaPrimary: {
            padding: '16px 32px',
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            border: 'none',
            color: '#ffffff',
            fontSize: '17px',
            fontWeight: 600,
            cursor: 'pointer',
            borderRadius: '12px',
            boxShadow: '0 8px 30px rgba(59, 130, 246, 0.4)',
            transition: 'transform 0.2s, box-shadow 0.2s'
        },
        ctaSecondary: {
            padding: '16px 32px',
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid #475569',
            color: '#e2e8f0',
            fontSize: '17px',
            fontWeight: 600,
            cursor: 'pointer',
            borderRadius: '12px',
            transition: 'all 0.2s'
        },
        statsGrid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '16px',
            maxWidth: '800px',
            margin: '0 auto'
        },
        statCard: {
            padding: '24px',
            background: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid #334155',
            borderRadius: '12px',
            textAlign: 'center'
        },
        statValue: {
            fontSize: '32px',
            fontWeight: 700,
            color: '#3b82f6',
            marginBottom: '4px'
        },
        statLabel: {
            fontSize: '13px',
            color: '#64748b'
        },
        section: {
            padding: '80px 24px',
            maxWidth: '1200px',
            margin: '0 auto'
        },
        sectionTitle: {
            fontSize: 'clamp(28px, 4vw, 40px)',
            fontWeight: 700,
            textAlign: 'center',
            marginBottom: '16px',
            color: '#ffffff'
        },
        sectionSubtitle: {
            fontSize: '16px',
            color: '#94a3b8',
            textAlign: 'center',
            maxWidth: '600px',
            margin: '0 auto 48px'
        },
        featuresGrid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px'
        },
        featureCard: {
            padding: '28px',
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid #334155',
            borderRadius: '16px',
            transition: 'transform 0.2s, border-color 0.2s'
        },
        featureIcon: {
            fontSize: '32px',
            marginBottom: '16px'
        },
        featureTitle: {
            fontSize: '18px',
            fontWeight: 600,
            color: '#ffffff',
            marginBottom: '8px'
        },
        featureDesc: {
            fontSize: '14px',
            lineHeight: 1.6,
            color: '#94a3b8'
        },
        ctaSection: {
            padding: '80px 24px',
            textAlign: 'center',
            background: 'linear-gradient(180deg, transparent, rgba(59, 130, 246, 0.05))'
        },
        footer: {
            padding: '32px 24px',
            borderTop: '1px solid #1e293b',
            textAlign: 'center'
        },
        footerText: {
            fontSize: '14px',
            color: '#64748b'
        }
    };

    return (
        <div style={styles.page}>
            {/* Navigation */}
            <nav style={styles.nav}>
                <div style={styles.navInner}>
                    <div style={styles.logo}>
                        <div style={styles.logoIcon}>⛏️</div>
                        <span style={styles.logoText}>MineOpt Pro</span>
                    </div>
                    <div style={styles.navButtons}>
                        <button
                            style={styles.navButtonSecondary}
                            onClick={() => navigate('/login')}
                            onMouseOver={e => e.target.style.color = '#ffffff'}
                            onMouseOut={e => e.target.style.color = '#94a3b8'}
                        >
                            Sign In
                        </button>
                        <button
                            style={styles.navButtonPrimary}
                            onClick={() => navigate('/register')}
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section style={styles.hero}>
                <div style={styles.badge}>
                    <div style={styles.badgeDot}></div>
                    <span style={styles.badgeText}>Enterprise Coal Mine Production Scheduling</span>
                </div>

                <h1 style={styles.heading}>
                    Optimize Your Mine.<br />
                    <span style={styles.headingAccent}>Every Shift.</span>
                </h1>

                <p style={styles.subheading}>
                    Advanced short-term scheduling that balances quality specs, equipment constraints,
                    and production targets. Make decisions operations recognizes, with explanations you can trust.
                </p>

                <div style={styles.ctaButtons}>
                    <button
                        style={styles.ctaPrimary}
                        onClick={() => navigate('/register')}
                        onMouseOver={e => e.target.style.transform = 'translateY(-2px)'}
                        onMouseOut={e => e.target.style.transform = 'translateY(0)'}
                    >
                        Start Free Trial
                    </button>
                    <button
                        style={styles.ctaSecondary}
                        onClick={() => navigate('/login')}
                        onMouseOver={e => {
                            e.target.style.background = 'rgba(51, 65, 85, 0.8)';
                            e.target.style.borderColor = '#64748b';
                        }}
                        onMouseOut={e => {
                            e.target.style.background = 'rgba(30, 41, 59, 0.8)';
                            e.target.style.borderColor = '#475569';
                        }}
                    >
                        Sign In →
                    </button>
                </div>

                {/* Stats */}
                <div style={styles.statsGrid}>
                    {stats.map((stat, idx) => (
                        <div key={idx} style={styles.statCard}>
                            <div style={styles.statValue}>{stat.value}</div>
                            <div style={styles.statLabel}>{stat.label}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Features Section */}
            <section style={styles.section}>
                <h2 style={styles.sectionTitle}>
                    Everything You Need for Optimal Operations
                </h2>
                <p style={styles.sectionSubtitle}>
                    A complete platform for short-term mine scheduling, from pit to product.
                </p>

                <div style={styles.featuresGrid}>
                    {features.map((feature, idx) => (
                        <div
                            key={idx}
                            style={styles.featureCard}
                            onMouseOver={e => {
                                e.currentTarget.style.transform = 'translateY(-4px)';
                                e.currentTarget.style.borderColor = '#475569';
                            }}
                            onMouseOut={e => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.borderColor = '#334155';
                            }}
                        >
                            <div style={styles.featureIcon}>{feature.icon}</div>
                            <h3 style={styles.featureTitle}>{feature.title}</h3>
                            <p style={styles.featureDesc}>{feature.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA Section */}
            <section style={styles.ctaSection}>
                <h2 style={{ ...styles.sectionTitle, marginBottom: '24px' }}>
                    Ready to Optimize Your Operations?
                </h2>
                <p style={{ ...styles.sectionSubtitle, marginBottom: '32px' }}>
                    Join mining operations worldwide using MineOpt Pro for smarter scheduling.
                </p>
                <div style={styles.ctaButtons}>
                    <button
                        style={styles.ctaPrimary}
                        onClick={() => navigate('/register')}
                    >
                        Get Started Free
                    </button>
                    <button
                        style={styles.ctaSecondary}
                        onClick={() => navigate('/login')}
                    >
                        Sign In
                    </button>
                </div>
            </section>

            {/* Footer */}
            <footer style={styles.footer}>
                <p style={styles.footerText}>
                    © 2026 MineOpt Pro. All rights reserved. • v2.1.0 Enterprise
                </p>
            </footer>
        </div>
    );
};

export default LandingPage;
