import {
  BadRequestException,
  Injectable,
  PipeTransform,
} from '@nestjs/common';

type SafeParseSchema<T> = {
  safeParse(value: unknown): {
    success: true;
    data: T;
  } | {
    success: false;
    error: { flatten(): unknown };
  };
};

@Injectable()
export class ZodValidationPipe<T> implements PipeTransform {
  constructor(private readonly schema: SafeParseSchema<T>) {}

  transform(value: unknown): T {
    const parsed = this.schema.safeParse(value);
    if (!parsed.success) {
      throw new BadRequestException({
        code: 'VALIDATION_ERROR',
        message: 'Validation failed',
        details: parsed.error.flatten(),
      });
    }
    return parsed.data;
  }
}
