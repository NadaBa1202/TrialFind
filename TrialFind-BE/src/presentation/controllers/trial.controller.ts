import { Body, Controller, Post, UseGuards } from '@nestjs/common';
import { SearchTrialsDto } from '../../application/dtos/trial/searchTrials.dto';
import { SearchTrialsUseCase } from '../../application/useCases/trial/search-trials.usecase';
import { AccessTokenGuard } from '../guards/jwt.guards';

@Controller('trials')
@UseGuards(AccessTokenGuard)
export class TrialController {
    constructor(private readonly searchTrialsUseCase: SearchTrialsUseCase) {}

    @Post('search')
    async search(@Body() dto: SearchTrialsDto) {
        return this.searchTrialsUseCase.execute(dto);
    }
}