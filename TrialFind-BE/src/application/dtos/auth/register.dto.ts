import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsOptional, IsString, Matches, MaxLength, MinLength } from 'class-validator';
import { SanitizeString } from '../../../presentation/decorators/Sanitize.decorator';

export class RegisterCaregiverDto {
    @ApiProperty()
    @SanitizeString()
    @IsEmail()
    @MaxLength(254)
    email: string;

    @ApiProperty({ description: 'Min 8 chars, at least one uppercase, one lowercase, one number and one symbol' })
    @IsString()
    @MinLength(8)
    @MaxLength(72) 
    @Matches(/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).+/, {
        message:
            'password must contain at least one uppercase letter, one lowercase letter, one number and one symbol',
    })
    password: string;

    @ApiProperty()
    @SanitizeString()
    @IsString()
    @MinLength(1)
    @MaxLength(80)
    firstName: string;

    @ApiProperty()
    @SanitizeString()
    @IsString()
    @MinLength(1)
    @MaxLength(80)
    lastName: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @Matches(/^\+?[0-9\s-]{7,20}$/, { message: 'phone must be a valid phone number' })
    phone?: string;
}