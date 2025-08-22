'use client';

import { useState } from 'react';
import { PaymentResponse } from '@/types/payment';

interface PaymentResultProps {
  result: PaymentResponse;
}

export default function PaymentResult({ result }: PaymentResultProps) {
  const [isTraceExpanded, setIsTraceExpanded] = useState(false);

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'allow':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'block':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'allow':
        return '✅';
      case 'review':
        return '⚠️';
      case 'block':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Payment Decision</h2>
      
      {/* Decision */}
      <div className="mb-6">
        <div className={`inline-flex items-center px-4 py-2 rounded-full border ${getDecisionColor(result.decision)}`}>
          <span className="text-2xl mr-2">{getDecisionIcon(result.decision)}</span>
          <span className="text-lg font-semibold capitalize">{result.decision}</span>
        </div>
        <p className="text-sm text-gray-600 mt-2">Request ID: {result.requestId}</p>
      </div>

      {/* Reasons */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Reasons</h3>
        <div className="space-y-2">
          {result.reasons.map((reason, index) => (
            <div key={index} className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span className="text-gray-700">{reason}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Trace */}
      <div>
        <button
          onClick={() => setIsTraceExpanded(!isTraceExpanded)}
          className="flex items-center justify-between w-full text-left text-lg font-semibold text-gray-800 mb-3 hover:text-blue-600 transition-colors"
        >
          <span>Agent Trace</span>
          <span className="text-blue-500">
            {isTraceExpanded ? '▼' : '▶'}
          </span>
        </button>
        
        {isTraceExpanded && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            {result.agentTrace.map((step, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800 mb-1">{step.step}</h4>
                    <p className="text-gray-600 text-sm">{step.detail}</p>
                  </div>
                  <span className="text-xs text-gray-500 ml-4">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
