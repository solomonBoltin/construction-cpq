
import React from 'react';
import { useQuoteBuilderStore } from '../../stores/useQuoteBuilderStore';
import { STEPS } from '../../config/quoteBuilder';
import { ComponentErrorBoundary } from '../common/ErrorBoundary';

const StepContentRenderer: React.FC = () => {
    const activeStep = useQuoteBuilderStore(state => state.activeStep);
    const step = STEPS.find(s => s.key === activeStep);
    
    if (!step) {
        return <div className="text-slate-500">Unknown step. Please select a valid step.</div>;
    }
    
    // Only render the active step component - this prevents all steps from mounting
    // and running their useEffect hooks simultaneously
    const Component = step.component;
    
    return (
        <ComponentErrorBoundary>
            <Component {...(step.props || {})} />
        </ComponentErrorBoundary>
    );
};

export default StepContentRenderer;
