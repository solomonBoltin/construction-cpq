
import React from 'react';
import { useQuoteBuilderStore } from '../../stores/useQuoteBuilderStore';
import { STEPS } from '../../config/quoteBuilder';

const StepContentRenderer: React.FC = () => {
    const activeStep = useQuoteBuilderStore(state => state.activeStep);
    const step = STEPS.find(s => s.key === activeStep);
    
    if (!step) {
        return <div className="text-slate-500">Unknown step. Please select a valid step.</div>;
    }
    
    const Component = step.component;
    return <Component {...(step.props || {})} />;
};

export default StepContentRenderer;
