import { Caregiver } from '../entities/caregiver.entity';
import { IRepository } from './IRepository.service';

export abstract class ICaregiverRepository extends IRepository<Caregiver> {
    abstract findByEmail(email: string): Promise<Caregiver | null>;
    abstract setRefreshTokenHash(id: string, hash: string | null): Promise<void>;
    abstract setPasswordResetToken(
        id: string,
        hash: string | null,
        expiresAt: Date | null,
    ): Promise<void>;
    abstract registerFailedLogin(id: string, lockedUntil: Date | null): Promise<void>;
    abstract resetFailedLogins(id: string): Promise<void>;
}