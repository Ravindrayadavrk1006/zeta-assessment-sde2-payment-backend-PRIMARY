import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PaymentForm from '../PaymentForm';

const mockOnSubmit = jest.fn();

describe('PaymentForm', () => {
  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<PaymentForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    expect(screen.getByLabelText(/customer id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/currency/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/payee id/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit payment/i })).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    render(<PaymentForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Fill out the form
    fireEvent.change(screen.getByLabelText(/customer id/i), { target: { value: 'customer123' } });
    fireEvent.change(screen.getByLabelText(/amount/i), { target: { value: '100.50' } });
    fireEvent.change(screen.getByLabelText(/payee id/i), { target: { value: 'payee456' } });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /submit payment/i }));
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        customerId: 'customer123',
        amount: 100.50,
        currency: 'USD',
        payeeId: 'payee456',
      });
    });
  });

  it('disables submit button when loading', () => {
    render(<PaymentForm onSubmit={mockOnSubmit} isLoading={true} />);
    
    const submitButton = screen.getByRole('button', { name: /processing/i });
    expect(submitButton).toBeDisabled();
  });

  it('disables submit button with invalid data', () => {
    render(<PaymentForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    const submitButton = screen.getByRole('button', { name: /submit payment/i });
    expect(submitButton).toBeDisabled();
    
    // Fill only some fields
    fireEvent.change(screen.getByLabelText(/customer id/i), { target: { value: 'customer123' } });
    expect(submitButton).toBeDisabled();
  });
});
