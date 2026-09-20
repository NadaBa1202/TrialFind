import { ApiProperty } from '@nestjs/swagger';
import { IsString, MaxLength } from 'class-validator';

export class SendEligibilityMessageDto {
    @ApiProperty()
    @IsString()
    @MaxLength(2000)
    message: string;
}