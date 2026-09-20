import {
    Body,
    Controller,
    HttpCode,
    HttpStatus,
    Post,
    Req,
    Res,
    UseGuards,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Throttle } from '@nestjs/throttler';
import { Request, Response } from 'express';
import { LoginDto } from '../../application/dtos/auth/login.dto';
import { RegisterCaregiverDto } from '../../application/dtos/auth/register.dto';
import { LoginUseCase } from '../../application/useCases/auth/login.usecase';
import { RefreshUseCase } from '../../application/useCases/auth/refresh.usecase';
import { RegisterUseCase } from '../../application/useCases/auth/register.usecase';
import { GetUser } from '../decorators/getUser.decorator';
import { AccessTokenGuard, RefreshTokenGuard } from '../guards/jwt.guards';

const REFRESH_COOKIE = 'refreshToken';

@Controller('auth')
export class AuthController {
    constructor(
        private readonly registerUseCase: RegisterUseCase,
        private readonly loginUseCase: LoginUseCase,
        private readonly refreshUseCase: RefreshUseCase,
        private readonly config: ConfigService,
    ) {}

    @Post('register')
    @Throttle({ default: { limit: 5, ttl: 60_000 } })
    async register(@Body() dto: RegisterCaregiverDto) {
        return this.registerUseCase.execute(dto);
    }

    @Post('login')
    @HttpCode(HttpStatus.OK)
    @Throttle({ default: { limit: 5, ttl: 60_000 } }) // slow brute-force attempts
    async login(@Body() dto: LoginDto, @Res({ passthrough: true }) res: Response) {
        const { accessToken, refreshToken, caregiver } = await this.loginUseCase.execute(dto);
        this.setRefreshCookie(res, refreshToken);
        return { accessToken, caregiver };
    }

    @Post('refresh')
    @HttpCode(HttpStatus.OK)
    @UseGuards(RefreshTokenGuard)
    async refresh(
        @GetUser() user: { id: string; refreshToken: string },
        @Res({ passthrough: true }) res: Response,
    ) {
        const { accessToken, refreshToken } = await this.refreshUseCase.execute(
            user.id,
            user.refreshToken,
        );
        this.setRefreshCookie(res, refreshToken);
        return { accessToken };
    }

    @Post('logout')
    @HttpCode(HttpStatus.OK)
    @UseGuards(RefreshTokenGuard)
    async logout(
        @GetUser('id') caregiverId: string,
        @Res({ passthrough: true }) res: Response,
    ) {
        await this.refreshUseCase.logout(caregiverId);
        res.clearCookie(REFRESH_COOKIE);
        return { loggedOut: true };
    }

    private setRefreshCookie(res: Response, refreshToken: string) {
        const isProd = this.config.get<string>('env') === 'production';
        res.cookie(REFRESH_COOKIE, refreshToken, {
            httpOnly: true,
            secure: isProd, // requires HTTPS in prod; allow http in local dev
            sameSite: 'strict',
            path: '/auth', // only sent back to auth endpoints
            maxAge: 7 * 24 * 60 * 60 * 1000,
        });
    }
}