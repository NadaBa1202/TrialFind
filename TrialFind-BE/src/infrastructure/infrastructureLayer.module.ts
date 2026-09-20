import { Module } from '@nestjs/common';
import { ICaregiverRepository } from '../domain/abstracts/ICaregiverRepository.service';
import { IPatientRepository } from '../domain/abstracts/IPatientRepository.service';
import { ITrialRepository } from '../domain/abstracts/ITrialRepository.service';
import { IEligibilitySessionRepository } from '../domain/abstracts/IEligibilitySessionRepository.service';
import { PrismaModule } from './database/postgresql/prisma.module';
import { CaregiverRepository } from './database/postgresql/repositories/caregiver.repository';
import { PatientRepository } from './database/postgresql/repositories/patient.repository';
import { TrialRepository } from './database/postgresql/repositories/trial.repository';
import { EligibilitySessionRepository } from './database/postgresql/repositories/eligibility-session.repository';
import { BcryptModule } from './bcrypt/bcrypt.module';
import { JwtModule } from './jwt/jwt.module';
import { AiModule } from './ai/ai.module';

@Module({
    imports: [PrismaModule, BcryptModule, JwtModule, AiModule],
    providers: [
        { provide: ICaregiverRepository, useClass: CaregiverRepository },
        { provide: IPatientRepository, useClass: PatientRepository },
        { provide: ITrialRepository, useClass: TrialRepository },
        { provide: IEligibilitySessionRepository, useClass: EligibilitySessionRepository },
        // NOTE: no `{ provide: IEligibilityAiService, useClass: AiModule }` here. That line
        // instantiated a *module class* as if it were the service (so `assess` was undefined).
        // AiModule already provides and exports IEligibilityAiService; we just re-export the module.
    ],
    exports: [
        BcryptModule,
        JwtModule,
        AiModule, // re-exports IEligibilityAiService to whoever imports this module
        ICaregiverRepository,
        IPatientRepository,
        ITrialRepository,
        IEligibilitySessionRepository,
    ],
})
export class InfrastructureLayerModule {}
