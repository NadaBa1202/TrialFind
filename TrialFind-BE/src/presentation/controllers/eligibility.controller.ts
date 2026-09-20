import { Body, Controller, Param, Post, UseGuards } from '@nestjs/common';
import { StartEligibilitySessionDto } from '../../application/dtos/eligibility/startEligibilitySession.dto';
import { SendEligibilityMessageDto } from '../../application/dtos/eligibility/sendEligibilityMessage.dto';
import { StartEligibilitySessionUseCase } from '../../application/useCases/eligibility/start-eligibility-session.usecase';
import { SendEligibilityMessageUseCase } from '../../application/useCases/eligibility/send-eligibility-message.usecase';
import { AccessTokenGuard } from '../guards/jwt.guards';

@Controller('eligibility')
@UseGuards(AccessTokenGuard)
export class EligibilityController {
    constructor(
        private readonly startSession: StartEligibilitySessionUseCase,
        private readonly sendMessage: SendEligibilityMessageUseCase,
    ) {}

    @Post('sessions')
    async start(@Body() dto: StartEligibilitySessionDto) {
        return this.startSession.execute(dto.patientId, dto.trialId);
    }

    @Post('sessions/:id/messages')
    async message(@Param('id') id: string, @Body() dto: SendEligibilityMessageDto) {
        return this.sendMessage.execute(id, dto.message);
    }
}