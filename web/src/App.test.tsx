import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
    it('renders PathPilot header', () => {
        render(<App />);
        expect(screen.getByText(/PathPilot/i)).toBeInTheDocument();
    });
});
