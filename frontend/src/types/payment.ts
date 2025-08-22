export interface PaymentRequest {
  customerId: string;
  amount: number;
  currency: 'USD' | 'EUR' | 'GBP' | 'JPY';
  payeeId: string;
  idempotencyKey: string;
}

export interface AgentStep {
  step: string;
  detail: string;
  timestamp: string;
}

export interface PaymentResponse {
  decision: 'allow' | 'review' | 'block';
  reasons: string[];
  agentTrace: AgentStep[];
  requestId: string;
}

export interface PaymentFormData {
  customerId: string;
  amount: number;
  currency: 'USD' | 'EUR' | 'GBP' | 'JPY';
  payeeId: string;
}
