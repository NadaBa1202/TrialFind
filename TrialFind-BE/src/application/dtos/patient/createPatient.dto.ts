import { ApiProperty } from '@nestjs/swagger';
import { IsDateString, IsEnum, IsOptional, IsString, MaxLength, MinLength } from 'class-validator';
import { Sex } from '../../../domain/enums/sex.enums';
import { SanitizeString } from '../../../presentation/decorators/sanitize.decorator';

export class CreatePatientDto {
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

    @ApiProperty({ example: '1954-03-12' })
    @IsDateString()
    dateOfBirth: string;

    @ApiProperty({ enum: Sex })
    @IsEnum(Sex)
    sex: Sex;

    @ApiProperty()
    @SanitizeString()
    @IsString()
    @MaxLength(60)
    relationshipToCaregiver: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @MaxLength(500)
    conditionSummary?: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @MaxLength(120)
    city?: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @MaxLength(120)
    region?: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @MaxLength(120)
    country?: string;
}