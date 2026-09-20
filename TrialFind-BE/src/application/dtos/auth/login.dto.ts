import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, MaxLength, MinLength } from 'class-validator';
import { SanitizeString } from '../../../presentation/decorators/sanitize.decorator';

export class LoginDto {
    @ApiProperty()
    @SanitizeString()
    @IsEmail()
    @MaxLength(254)
    email: string;

    @ApiProperty()
    @IsString()
    @MinLength(1)
    @MaxLength(72)
    password: string;
}