import { HttpStatus } from '@nestjs/common';
import { BaseException } from './base.exception';

export class AuthException extends BaseException {
    // Deliberately identical wording for "no such user" and "wrong password" —
    // never let a caller distinguish the two (prevents account enumeration).
    static invalidCredentials(): AuthException {
        return new AuthException('Invalid email or password.', HttpStatus.UNAUTHORIZED);
    }

    static accountLocked(): AuthException {
        return new AuthException(
            'Too many failed login attempts. Try again later.',
            HttpStatus.TOO_MANY_REQUESTS,
        );
    }

    static emailAlreadyRegistered(): AuthException {
        return new AuthException('An account with this email already exists.', HttpStatus.CONFLICT);
    }

    static invalidOrExpiredToken(): AuthException {
        return new AuthException('Invalid or expired token.', HttpStatus.UNAUTHORIZED);
    }
}