import { Module } from '@nestjs/common';
import { JwtModule as NestJwtModule } from '@nestjs/jwt';
import { IJwtService } from '../../domain/abstracts/IJwt.service';
import { JwtServiceImpl } from './jwt.service';

@Module({
    imports: [NestJwtModule.register({})], // secrets are supplied per-call in JwtServiceImpl
    providers: [{ provide: IJwtService, useClass: JwtServiceImpl }],
    exports: [IJwtService],
})
export class JwtModule {}