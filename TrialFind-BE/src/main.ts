import { ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import * as cookieParser from 'cookie-parser';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { HttpExceptionFilter } from './presentation/filters/http-exception.filter';
import { ResponseInterceptor } from './presentation/interceptors/response.interceptor';

async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    const config = app.get(ConfigService);

    // --- security headers ---
    app.use(helmet());

    // --- signed, httpOnly cookies (refresh token lives here) ---
    app.use(cookieParser(config.get<string>('cookieSecret')));

    // --- strict input validation: unknown fields are rejected outright ---
    app.useGlobalPipes(
        new ValidationPipe({
            whitelist: true,
            forbidNonWhitelisted: true,
            transform: true,
            transformOptions: { enableImplicitConversion: true },
        }),
    );

    app.useGlobalFilters(new HttpExceptionFilter(config));
    app.useGlobalInterceptors(new ResponseInterceptor());

    // --- CORS: explicit allow-list only, required since we send credentialed cookies ---
    app.enableCors({
        origin: config.get<string[]>('cors.origin'),
        credentials: true,
        methods: ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
    });

    if (config.get<string>('env') !== 'production') {
        const swaggerConfig = new DocumentBuilder()
            .setTitle('TrialBridge API')
            .setDescription('Clinical trial eligibility matching — caregiver & patient management')
            .addBearerAuth()
            .setVersion('1.0')
            .build();
        const document = SwaggerModule.createDocument(app, swaggerConfig);
        SwaggerModule.setup('api/docs', app, document);
    }

    await app.listen(config.get<number>('port'));
}

bootstrap();