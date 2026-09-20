import { Base } from './base.entity';

export class Caregiver extends Base {
    email: string;
    password: string; // bcrypt hash

    firstName: string;
    lastName: string;
    phone?: string | null;

    isEmailVerified: boolean;

    refreshTokenHash?: string | null;
    passwordResetTokenHash?: string | null;
    passwordResetExpiresAt?: Date | null;
    failedLoginAttempts: number;
    lockedUntil?: Date | null;

    isLocked(): boolean {
        return !!this.lockedUntil && this.lockedUntil.getTime() > Date.now();
    }

    /** Strip every security-sensitive field before returning this over the API. */
    toSafeProfile() {
        return {
            id: this.id,
            email: this.email,
            firstName: this.firstName,
            lastName: this.lastName,
            phone: this.phone ?? null,
            isEmailVerified: this.isEmailVerified,
            createdAt: this.createdAt,
        };
    }
}