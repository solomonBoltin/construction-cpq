import React, { useCallback } from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import { useStepNavigation } from '../../../hooks/useStepNavigation';
import { MaterializedProductEntry, ProductRole } from '../../../types';
import LoadingSpinner from '../../common/LoadingSpinner';
import { shortUnitType } from '../../../utils/units';
import { debounce } from '../../../utils/debounce'; 

interface ProductConfiguratorStepProps {
    role: ProductRole.MAIN | ProductRole.SECONDARY;
}

const ProductConfiguratorStep: React.FC<ProductConfiguratorStepProps> = ({ role }) => {
    const { 
        quote, 
        updateProductQuantity, 
        updateProductVariation, 
        isLoading: contextLoading,
        error: contextError,
    } = useQuoteBuilderStore();
    const { goToStep } = useStepNavigation();

    // Find the entry that matches the role directly from the context
    const productEntry = quote?.product_entries.find(e => e.role === role) as MaterializedProductEntry | undefined;

    // Debounced quantity update
    const debouncedUpdateQuantity = useCallback(
        debounce((entryId: number, quantity: number) => {
            updateProductQuantity(entryId, quantity);
        }, 500),
        [updateProductQuantity]
    );

    if (!productEntry?.id) {
         return (
            <div className="text-center p-8 bg-white rounded-lg shadow">
                 <h3 className="font-bold text-lg text-slate-700">No product selected for configuration.</h3>
                 <p className="text-sm text-slate-500">Please select a {role === ProductRole.MAIN ? 'main product' : 'secondary product'} first.</p>
                 <button 
                    onClick={() => goToStep(role === ProductRole.MAIN ? 'choose_main_product' : 'choose_secondary_product')} 
                    className="mt-4 bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
                >
                    Select {role === ProductRole.MAIN ? 'Main Product' : 'Secondary Product'}
                 </button>
            </div>
        );
    }
    
    const currentLoading = contextLoading;
    const currentError = contextError;

    if (currentLoading) return <LoadingSpinner />;
    if (currentError && !productEntry) return <div className="text-red-500 p-4 bg-red-50 rounded-md">Error: {currentError}</div>;
    if (!productEntry) {
         return <div className="text-slate-500 p-4">Select a product to configure its options.</div>;
    }

    return (
        <div className="fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Configure: {productEntry.product_name}</h2>
            <p className="text-slate-600 mb-6">Set the quantity and options for this item ({productEntry.role?.toLowerCase()}).</p>
            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                    <div>
                        <label htmlFor={`quantity-${productEntry.id}`} className="block text-sm font-medium text-slate-700 mb-1">
                            Quantity ({shortUnitType(productEntry.product_unit)})
                        </label>
                        <input 
                            type="number" 
                            id={`quantity-${productEntry.id}`}
                            defaultValue={productEntry.quantity_of_product_units}
                            onChange={(e) => debouncedUpdateQuantity(productEntry.id, parseFloat(e.target.value) || 0)}
                            className="w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    {productEntry.variation_groups.map(group => (
                        <div key={group.id}>
                            <h4 className="text-sm font-medium text-slate-700 mb-2">
                                {group.name} {group.is_required ? <span className="text-red-500">*</span> : ''}
                            </h4>
                            {group.options.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {group.options.map(opt => (
                                        <button 
                                            key={opt.id}
                                            onClick={() => updateProductVariation(productEntry.id, group.id, opt.id)}
                                            className={`px-3 py-1.5 text-sm font-medium rounded-md border transition-colors
                                                        ${opt.is_selected ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}`}
                                        >
                                            {opt.name} {parseFloat(opt.additional_price) > 0 ? `(+$${opt.additional_price})` : ''}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-slate-400 italic">No options for this group (e.g. requires input).</p>
                            )}
                        </div>
                    ))}
                </div>

                <div className="mt-8 border-t pt-6 flex justify-end">
                    <button 
                        onClick={() => goToStep(role === ProductRole.MAIN ? 'choose_secondary_product' : 'select_additional')}
                        className="bg-blue-600 text-white font-semibold py-2 px-5 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
                    >
                        Next Step
                    </button>
                </div>
            </div>
        </div>
    );
};


export default ProductConfiguratorStep;
