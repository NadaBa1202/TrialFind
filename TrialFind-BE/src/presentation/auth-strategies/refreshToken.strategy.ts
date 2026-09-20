import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ConfigService } from '@nestjs/config';
import { Strategy } from 'passport-jwt';
import { Request } from 'express';

const cookieExtractor = (req: Request): string | null => {
    return req?.cookies?.refreshToken ?? null;
};

@Injectable()
export class RefreshTokenStrategy extends PassportStrategy(Strategy, 'jwt-refresh') {
    constructor(private readonly config: ConfigService) {
        super({
            jwtFromRequest: cookieExtractor,
            ignoreExpiration: false,
            secretOrKey: config.get<string>('jwt.refresh.secret'),
            passReqToCallback: true,
        });
    }

    async validate(req: Request, payload: { sub: string }) {
        return { id: payload.sub, refreshToken: cookieExtractor(req) };
    }
}