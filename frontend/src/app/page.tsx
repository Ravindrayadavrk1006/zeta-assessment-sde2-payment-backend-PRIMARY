'use client';

import { useState } from 'react';
import PaymentForm from '@/components/PaymentForm';
import PaymentResult from '@/components/PaymentResult';
import { PaymentFormData, PaymentResponse } from '@/types/payment';
import { submitPayment } from '@/utils/payment';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PaymentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: PaymentFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await submitPayment(formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">PayNow</h1>
          <p className="text-lg text-gray-600">AI-Powered Payment Decision System</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Payment Form */}
          <div>
            <PaymentForm onSubmit={handleSubmit} isLoading={isLoading} />
            
            {/* Error Display */}
            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-red-400">⚠️</span>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Payment Result */}
          <div>
            {result ? (
              <PaymentResult result={result} />
            ) : (
              <div className="bg-white rounded-lg shadow-md p-6 text-center">
                <div className="text-gray-400 text-6xl mb-4">💳</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Submit a Payment</h3>
                <p className="text-gray-500">
                  Fill out the form and submit to see the AI decision, reasons, and agent trace.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Built with Next.js, TypeScript, and Tailwind CSS</p>
          <p className="mt-1">Integrates with FastAPI backend for AI-powered payment decisions</p>
        </div>
      </div>
    </div>
  );
}
