import { Module } from '@nestjs/common';
import { PassportModule } from '@nestjs/passport';
import { ApplicationLayerModule } from '../application/applicationLayer.module';
import { InfrastructureLayerModule } from '../infrastructure/infrastructureLayer.module';
import { AccessTokenStrategy } from './auth-strategies/accessToken.strategy';
import { RefreshTokenStrategy } from './auth-strategies/refreshToken.strategy';
import { AuthController } from './controllers/auth.controller';
import { PatientController } from './controllers/patient.controller';
import { TrialController } from './controllers/trial.controller';
import { EligibilityController } from './controllers/eligibility.controller';

@Module({
    imports: [PassportModule, ApplicationLayerModule, InfrastructureLayerModule],
    controllers: [AuthController, PatientController, TrialController, EligibilityController],
    providers: [AccessTokenStrategy, RefreshTokenStrategy],
})
export class PresentationLayerModule {}