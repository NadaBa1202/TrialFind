import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { APP_GUARD } from '@nestjs/core';
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';
import { ApplicationLayerModule } from './application/applicationLayer.module';
import configuration from './infrastructure/config';
import { InfrastructureLayerModule } from './infrastructure/infrastructureLayer.module';
import { PresentationLayerModule } from './presentation/presentationLayer.module';

const REQUIRED_ENV_VARS = [
    'DATABASE_URL',
    'JWT_ACCESS_SECRET',
    'JWT_REFRESH_SECRET',
    'JWT_RESET_SECRET',
];

function validateEnv(env: Record<string, unknown>) {
    const missing = REQUIRED_ENV_VARS.filter((key) => !env[key]);
    if (missing.length) {
        // Fail fast at boot rather than limping along with undefined secrets.
        throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
    return env;
}

@Module({
    imports: [
        ConfigModule.forRoot({
            isGlobal: true,
            expandVariables: true,
            load: [configuration],
            envFilePath: '.env',
            validate: validateEnv,
        }),
        ThrottlerModule.forRoot([{ ttl: 60_000, limit: 60 }]), // sane global default; endpoints override with @Throttle
        ApplicationLayerModule,
        PresentationLayerModule,
        InfrastructureLayerModule,
    ],
    providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }],
})
export class AppModule {}