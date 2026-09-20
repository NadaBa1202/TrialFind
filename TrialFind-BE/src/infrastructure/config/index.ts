export default () => ({
    env: process.env.NODE_ENV,
    port: parseInt(process.env.PORT, 10) || 5555,

    database: {
        url: process.env.DATABASE_URL,
    },

    jwt: {
        access: {
            secret: process.env.JWT_ACCESS_SECRET,
            expiresIn: process.env.JWT_ACCESS_EXPIRES_IN || '15m',
        },
        refresh: {
            secret: process.env.JWT_REFRESH_SECRET,
            expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
        },
        reset: {
            secret: process.env.JWT_RESET_SECRET,
            expiresIn: process.env.JWT_RESET_EXPIRES_IN || '15m',
        },
    },
    ai: {
        baseUrl: process.env.TRIALBRIDGE_AI_URL || 'http://localhost:8000',
        // must match AI_SERVICE_KEY on the Python side
        apiKey: process.env.TRIALBRIDGE_AI_KEY,
        timeoutMs: parseInt(process.env.TRIALBRIDGE_AI_TIMEOUT_MS, 10) || 120_000,
    },

    security: {
        bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS, 10) || 12,
    },

    cors: {
        origin: (process.env.CORS_ORIGIN || '').split(',').filter(Boolean),
    },

    cookieSecret: process.env.COOKIE_SECRET,
});
