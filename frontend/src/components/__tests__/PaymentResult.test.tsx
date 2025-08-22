import { render, screen, fireEvent } from '@testing-library/react';
import PaymentResult from '../PaymentResult';

const mockResult = {
  decision: 'review' as const,
  reasons: ['recent_disputes', 'amount_above_daily_threshold'],
  agentTrace: [
    {
      step: 'plan',
      detail: 'Check balance, risk, and limits',
      timestamp: '2024-01-01T10:00:00Z'
    },
    {
      step: 'tool:getBalance',
      detail: 'balance=300.00',
      timestamp: '2024-01-01T10:00:01Z'
    }
  ],
  requestId: 'req_abc123'
};

describe('PaymentResult', () => {
  it('renders decision with correct styling', () => {
    render(<PaymentResult result={mockResult} />);
    
    expect(screen.getByText('review')).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
    expect(screen.getByText('Request ID: req_abc123')).toBeInTheDocument();
  });

  it('renders all reasons', () => {
    render(<PaymentResult result={mockResult} />);
    
    expect(screen.getByText('recent_disputes')).toBeInTheDocument();
    expect(screen.getByText('amount_above_daily_threshold')).toBeInTheDocument();
  });

  it('shows agent trace when expanded', () => {
    render(<PaymentResult result={mockResult} />);
    
    // Initially trace should be collapsed
    expect(screen.queryByText('Check balance, risk, and limits')).not.toBeInTheDocument();
    
    // Click to expand
    fireEvent.click(screen.getByText('Agent Trace'));
    
    // Now trace should be visible
    expect(screen.getByText('Check balance, risk, and limits')).toBeInTheDocument();
    expect(screen.getByText('balance=300.00')).toBeInTheDocument();
  });

  it('toggles agent trace expansion', () => {
    render(<PaymentResult result={mockResult} />);
    
    const traceButton = screen.getByText('Agent Trace');
    
    // Initially collapsed
    expect(screen.getByText('▶')).toBeInTheDocument();
    
    // Click to expand
    fireEvent.click(traceButton);
    expect(screen.getByText('▼')).toBeInTheDocument();
    
    // Click to collapse
    fireEvent.click(traceButton);
    expect(screen.getByText('▶')).toBeInTheDocument();
  });

  it('displays different decision colors correctly', () => {
    const { rerender } = render(<PaymentResult result={mockResult} />);
    
    // Review decision (yellow)
    const reviewElement = screen.getByText('review').closest('div');
    expect(reviewElement).toHaveClass('bg-yellow-100');
    
    // Allow decision (green)
    rerender(<PaymentResult result={{ ...mockResult, decision: 'allow' }} />);
    const allowElement = screen.getByText('allow').closest('div');
    expect(allowElement).toHaveClass('bg-green-100');
    
    // Block decision (red)
    rerender(<PaymentResult result={{ ...mockResult, decision: 'block' }} />);
    const blockElement = screen.getByText('block').closest('div');
    expect(blockElement).toHaveClass('bg-red-100');
  });
});
