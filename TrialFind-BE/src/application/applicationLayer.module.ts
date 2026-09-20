import { Module } from '@nestjs/common';
import { InfrastructureLayerModule } from '../infrastructure/infrastructureLayer.module';
import { CaregiverFactory } from './factoryMapper/caregiver.factory';
import { PatientFactory } from './factoryMapper/patient.factory';
import { LoginUseCase } from './useCases/auth/login.usecase';
import { RefreshUseCase } from './useCases/auth/refresh.usecase';
import { RegisterUseCase } from './useCases/auth/register.usecase';
import { CreatePatientUseCase } from './useCases/patient/create-patient.usecase';
import { SearchTrialsUseCase } from './useCases/trial/search-trials.usecase';
import { StartEligibilitySessionUseCase } from './useCases/eligibility/start-eligibility-session.usecase';
import { SendEligibilityMessageUseCase } from './useCases/eligibility/send-eligibility-message.usecase';

@Module({
    imports: [InfrastructureLayerModule],
    providers: [
        CaregiverFactory,
        PatientFactory,
        RegisterUseCase,
        LoginUseCase,
        RefreshUseCase,
        CreatePatientUseCase,
        SearchTrialsUseCase,
        StartEligibilitySessionUseCase,
        SendEligibilityMessageUseCase,
    ],
    exports: [
        RegisterUseCase,
        LoginUseCase,
        RefreshUseCase,
        CreatePatientUseCase,
        SearchTrialsUseCase,
        StartEligibilitySessionUseCase,
        SendEligibilityMessageUseCase,
    ],
})
export class ApplicationLayerModule {}