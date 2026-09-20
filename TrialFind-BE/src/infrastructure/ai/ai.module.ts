import { Module } from '@nestjs/common';
import { IEligibilityAiService } from '../../domain/abstracts/IEligibilityAi.service';
import { EligibilityAiService } from './eligibilityAi.service';

@Module({
    providers: [{ provide: IEligibilityAiService, useClass: EligibilityAiService }],
    exports: [IEligibilityAiService],
})
export class AiModule {}