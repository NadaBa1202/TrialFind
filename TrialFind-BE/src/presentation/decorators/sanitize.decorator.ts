import { Transform } from 'class-transformer';


export function SanitizeString() {
    return Transform(({ value }) => {
        if (typeof value !== 'string') return value;
        // eslint-disable-next-line no-control-regex
        return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '').trim();
    });
}