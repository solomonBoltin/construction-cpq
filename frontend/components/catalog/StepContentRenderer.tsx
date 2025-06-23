
import React from 'react';
import { useQuoteProcess } from '../../contexts/QuoteProcessContext';
import CategorySelectorStep from './steps/CategorySelectorStep';
import ProductSelectorStep from './steps/ProductSelectorStep';
import ProductConfiguratorStep from './steps/ProductConfiguratorStep';
import AdditionalProductSelectorStep from './steps/AdditionalProductSelectorStep';
import ReviewStep from './steps/ReviewStep';
import { ProductRole } from '../../types';

const StepContentRenderer: React.FC = () => {
    const { activeStep } = useQuoteProcess();

    switch (activeStep) {
        case 'choose_category':
            return <CategorySelectorStep />;
        case 'choose_main_product':
            return <ProductSelectorStep role={ProductRole.MAIN} />;
        case 'configure_main':
            return <ProductConfiguratorStep role={ProductRole.MAIN} />;
        case 'choose_secondary_product':
            return <ProductSelectorStep role={ProductRole.SECONDARY} />;
        case 'configure_secondary':
            return <ProductConfiguratorStep role={ProductRole.SECONDARY} />;
        case 'select_additional':
            return <AdditionalProductSelectorStep />;
        case 'review':
            return <ReviewStep />;
        default:
            return <div className="text-slate-500">Unknown step. Please select a valid step.</div>;
    }
};

export default StepContentRenderer;
