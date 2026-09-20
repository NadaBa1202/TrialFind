import { Injectable } from '@nestjs/common';
import { Caregiver } from '../../domain/entities/caregiver.entity';

@Injectable()
export class CaregiverFactory {
    createNewCaregiver(params: {
        email: string;
        passwordHash: string;
        firstName: string;
        lastName: string;
        phone?: string;
    }): Partial<Caregiver> {
        return {
            email: params.email.toLowerCase(),
            password: params.passwordHash,
            firstName: params.firstName,
            lastName: params.lastName,
            phone: params.phone ?? null,
            isEmailVerified: false,
            failedLoginAttempts: 0,
        };
    }
}