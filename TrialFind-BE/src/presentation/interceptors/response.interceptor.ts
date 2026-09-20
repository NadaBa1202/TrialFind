import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export type Response<T> = {
    status: boolean;
    statusCode: number;
    message: string;
    data: T;
    timestamp: string;
};

@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, Response<T>> {
    intercept(context: ExecutionContext, next: CallHandler): Observable<Response<T>> {
        return next.handle().pipe(
            map((data) => {
                const ctx = context.switchToHttp();
                const response = ctx.getResponse();
                return {
                    status: true,
                    statusCode: response.statusCode,
                    message: 'success',
                    data,
                    timestamp: new Date().toISOString(),
                };
            }),
        );
    }
}