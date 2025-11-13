/**
 * Sophisticated logging utility with environment-aware behavior
 * In production, errors are sent to monitoring service (optional)
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
  prefix?: string;
}

class Logger {
  private config: LoggerConfig = {
    enabled: import.meta.env.DEV,
    level: 'info',
    prefix: '[VintedBot]',
  };

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;

    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const requestedLevelIndex = levels.indexOf(level);

    return requestedLevelIndex >= currentLevelIndex;
  }

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const prefix = this.config.prefix || '';
    let formatted = `${prefix} [${timestamp}] [${level.toUpperCase()}] ${message}`;

    if (data !== undefined) {
      formatted += `\n${JSON.stringify(data, null, 2)}`;
    }

    return formatted;
  }

  debug(message: string, data?: any): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatMessage('debug', message, data));
    }
  }

  info(message: string, data?: any): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message, data));
    }
  }

  warn(message: string, data?: any): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message, data));
    }
  }

  error(message: string, error?: any): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message, error));

      // In production, send to monitoring service
      if (!import.meta.env.DEV && typeof error === 'object') {
        this.sendToMonitoring(message, error);
      }
    }
  }

  private sendToMonitoring(message: string, error: any): void {
    // TODO: Integrate with Sentry, LogRocket, or similar
    // For now, just log to console in production
    if (import.meta.env.PROD) {
      // Example: Sentry.captureException(error, { extra: { message } });
    }
  }

  configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

export const logger = new Logger();
