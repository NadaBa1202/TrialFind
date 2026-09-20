import {
    ArgumentsHost,
    Catch,
    ExceptionFilter,
    HttpException,
    HttpStatus,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Response } from 'express';

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
    constructor(private readonly config: ConfigService) {}

    catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const response = ctx.getResponse<Response>();

        const isHttpException = exception instanceof HttpException;
        const status = isHttpException
            ? exception.getStatus()
            : HttpStatus.INTERNAL_SERVER_ERROR;

        const message = isHttpException
            ? exception.getResponse()
            : 'Internal server error';

        const isProd = this.config.get<string>('env') === 'production';

        response.status(status).json({
            status: false,
            statusCode: status,
            message,
            timestamp: new Date().toISOString(),
            // don't leak stack traces in prod
            ...(isProd ? {} : { stack: exception instanceof Error ? exception.stack : undefined }),
        });
    }
}