'use client';

import { useState } from 'react';
import { PaymentFormData } from '@/types/payment';

interface PaymentFormProps {
  onSubmit: (data: PaymentFormData) => void;
  isLoading: boolean;
}

export default function PaymentForm({ onSubmit, isLoading }: PaymentFormProps) {
  const [formData, setFormData] = useState<PaymentFormData>({
    customerId: '',
    amount: 0,
    currency: 'USD',
    payeeId: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.amount > 0 && formData.customerId && formData.payeeId) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof PaymentFormData, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Payment Request</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="customerId" className="block text-sm font-medium text-gray-700 mb-2">
            Customer ID
          </label>
          <input
            type="text"
            id="customerId"
            value={formData.customerId}
            onChange={(e) => handleInputChange('customerId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter customer ID"
            required
            pattern="^[a-zA-Z0-9_-]+$"
            minLength={3}
          />
          <p className="text-xs text-gray-500 mt-1">Alphanumeric characters, hyphens, and underscores only</p>
        </div>

        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
            Amount
          </label>
          <input
            type="number"
            id="amount"
            value={formData.amount}
            onChange={(e) => handleInputChange('amount', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
            step="0.01"
            min="0.01"
            max="1000000"
            required
          />
          <p className="text-xs text-gray-500 mt-1">Maximum amount: $1,000,000</p>
        </div>

        <div>
          <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-2">
            Currency
          </label>
          <select
            id="currency"
            value={formData.currency}
            onChange={(e) => handleInputChange('currency', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
            <option value="JPY">JPY</option>
          </select>
        </div>

        <div>
          <label htmlFor="payeeId" className="block text-sm font-medium text-gray-700 mb-2">
            Payee ID
          </label>
          <input
            type="text"
            id="payeeId"
            value={formData.payeeId}
            onChange={(e) => handleInputChange('payeeId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter payee ID"
            required
            pattern="^[a-zA-Z0-9_-]+$"
            minLength={3}
          />
          <p className="text-xs text-gray-500 mt-1">Alphanumeric characters, hyphens, and underscores only</p>
        </div>

        <button
          type="submit"
          disabled={isLoading || !formData.customerId || !formData.payeeId || formData.amount <= 0}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Processing...' : 'Submit Payment'}
        </button>
      </form>
    </div>
  );
}
