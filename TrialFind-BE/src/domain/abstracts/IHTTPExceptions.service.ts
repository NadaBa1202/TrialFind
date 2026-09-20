
export abstract class IHTTPException {
    abstract getInstance(): IHTTPException;

    abstract NotFound(id?: string): IHTTPException;

    abstract Unauthorized(message: string): IHTTPException;

    abstract Forbidden(message: string): IHTTPException;

    abstract BadRequest(message: string): IHTTPException;

    abstract Conflict(message: string): IHTTPException;
}