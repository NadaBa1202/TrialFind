import { Injectable, NotFoundException } from '@nestjs/common';
import { IEligibilitySessionRepository } from '../../../domain/abstracts/IEligibilitySessionRepository.service';
import { ITrialRepository } from '../../../domain/abstracts/ITrialRepository.service';

@Injectable()
export class StartEligibilitySessionUseCase {
    constructor(
        private readonly sessionRepository: IEligibilitySessionRepository,
        private readonly trialRepository: ITrialRepository,
    ) {}

    async execute(patientId: string, trialId: string) {
        const trial = await this.trialRepository.findById(trialId);
        if (!trial) throw new NotFoundException('Trial not found');

        const session = await this.sessionRepository.create(patientId, trialId);
        const intro = `Let's check eligibility for "${trial.title}". Tell me about the patient's diagnosis, recent cognitive test scores (e.g. MMSE/MoCA/CDR), current medications, and any study-partner support available.`;
        await this.sessionRepository.addMessage(session.id, 'ASSISTANT', intro);

        return { sessionId: session.id, assistantMessage: intro };
    }
}