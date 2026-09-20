import { ApiProperty } from '@nestjs/swagger';
import { IsString } from 'class-validator';

export class StartEligibilitySessionDto {
    @ApiProperty()
    @IsString()
    patientId: string;

    @ApiProperty()
    @IsString()
    trialId: string;
}