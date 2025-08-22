import { PaymentRequest, PaymentResponse } from '@/types/payment';

export const generateIdempotencyKey = (): string => {
  return `idem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const submitPayment = async (formData: Omit<PaymentRequest, 'idempotencyKey'>): Promise<PaymentResponse> => {
  const request: PaymentRequest = {
    ...formData,
    idempotencyKey: generateIdempotencyKey(),
  };

  const response = await fetch('http://127.0.0.1:8000/payments/decide', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'secret-test-key', // This should come from environment variables in production
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};
