import { Body, Controller, Get, NotFoundException, Param, Post, UseGuards } from '@nestjs/common';
import { CreatePatientDto } from '../../application/dtos/patient/createPatient.dto';
import { CreatePatientUseCase } from '../../application/useCases/patient/create-patient.usecase';
import { IPatientRepository } from '../../domain/abstracts/IPatientRepository.service';
import { GetUser } from '../decorators/getUser.decorator';
import { AccessTokenGuard } from '../guards/jwt.guards';

@Controller('patients')
@UseGuards(AccessTokenGuard)
export class PatientController {
    constructor(
        private readonly createPatientUseCase: CreatePatientUseCase,
        private readonly patientRepository: IPatientRepository,
    ) {}

    @Post()
    async create(@Body() dto: CreatePatientDto, @GetUser('id') caregiverId: string) {
        return this.createPatientUseCase.execute(dto, caregiverId);
    }

    @Get()
    async findAll(@GetUser('id') caregiverId: string) {
        return this.patientRepository.findAllByCaregiver(caregiverId);
    }

    @Get(':id')
    async findOne(@Param('id') id: string, @GetUser('id') caregiverId: string) {
        const patient = await this.patientRepository.findByIdAndCaregiver(id, caregiverId);
        if (!patient) throw new NotFoundException('Patient not found');
        return patient;
    }
}