import { Injectable } from '@nestjs/common';
import { AuthException } from '../../exceptions/auth.exception';
import { ICaregiverRepository } from '../../../domain/abstracts/ICaregiverRepository.service';
import { RegisterCaregiverDto } from '../../dtos/auth/register.dto';
import { CaregiverFactory } from '../../factoryMapper/caregiver.factory';
import { IHashService } from '../../../domain/abstracts/IHash.service';

@Injectable()
export class RegisterUseCase {
    constructor(
        private readonly caregiverRepository: ICaregiverRepository,
        private readonly caregiverFactory: CaregiverFactory,
        private readonly hashService: IHashService,
    ) {}

    async execute(dto: RegisterCaregiverDto) {
        const existing = await this.caregiverRepository.findByEmail(dto.email);
        if (existing) {
            throw AuthException.emailAlreadyRegistered();
        }

        const passwordHash = await this.hashService.hash(dto.password);
        const newCaregiver = this.caregiverFactory.createNewCaregiver({
            email: dto.email,
            passwordHash,
            firstName: dto.firstName,
            lastName: dto.lastName,
            phone: dto.phone,
        });

        const created = await this.caregiverRepository.create(newCaregiver);
        return created.toSafeProfile();
    }
}