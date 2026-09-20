import { ApiProperty } from '@nestjs/swagger';
import { IsArray, IsEnum, IsInt, IsOptional, IsString, Max, MaxLength, Min } from 'class-validator';
import { Sex } from '../../../domain/enums/sex.enums';
import { SanitizeString } from '../../../presentation/decorators/sanitize.decorator';

export class SearchTrialsDto {
    @ApiProperty()
    @IsInt()
    @Min(0)
    @Max(120)
    age: number;

    @ApiProperty({ enum: Sex })
    @IsEnum(Sex)
    sex: Sex;

    @ApiProperty()
    @SanitizeString()
    @IsString()
    @MaxLength(200)
    condition: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @SanitizeString()
    @IsString()
    @MaxLength(120)
    stage?: string;

    @ApiProperty({ required: false, type: [String] })
    @IsOptional()
    @IsArray()
    @IsString({ each: true })
    locations?: string[];
}