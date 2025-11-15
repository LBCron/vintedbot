/**
 * Design Tokens - VintedBot Modern UI
 * Glass-morphism + Gradients style (Notion/Linear/Arc inspired)
 */

export const designTokens = {
  colors: {
    background: {
      primary: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      secondary: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      tertiary: 'linear-gradient(135deg, #334155 0%, #475569 100%)',
    },
    accent: {
      primary: 'linear-gradient(135deg, #a855f7 0%, #7e22ce 100%)',
      hover: 'linear-gradient(135deg, #9333ea 0%, #6b21a8 100%)',
      light: 'linear-gradient(135deg, #c084fc 0%, #a855f7 100%)',
    },
    glass: {
      card: 'rgba(255, 255, 255, 0.05)',
      cardHover: 'rgba(255, 255, 255, 0.08)',
      border: 'rgba(255, 255, 255, 0.1)',
      borderHover: 'rgba(255, 255, 255, 0.2)',
    },
    text: {
      primary: '#ffffff',
      secondary: '#e2e8f0',
      tertiary: '#94a3b8',
      muted: '#64748b',
    },
  },

  shadows: {
    glow: '0 0 40px rgba(168, 85, 247, 0.3)',
    glowStrong: '0 0 60px rgba(168, 85, 247, 0.5)',
    card: '0 20px 50px rgba(0, 0, 0, 0.3)',
    cardHover: '0 30px 60px rgba(0, 0, 0, 0.4)',
    inner: 'inset 0 1px 2px rgba(0, 0, 0, 0.1)',
  },

  blur: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },

  animations: {
    transition: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    transitionSlow: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
    spring: {
      type: "spring" as const,
      stiffness: 300,
      damping: 30,
    },
    springGentle: {
      type: "spring" as const,
      stiffness: 200,
      damping: 25,
    },
  },

  borderRadius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    full: '9999px',
  },

  spacing: {
    card: '24px',
    section: '32px',
    page: '48px',
  },
};

export type DesignTokens = typeof designTokens;
