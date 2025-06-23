import React, { useEffect, useState, useCallback } from 'react';
import { useQuoteProcess } from '../../../contexts/QuoteProcessContext';
import { apiClient } from '../../../services/api';
import { ProductPreview, ProductRole } from '../../../types';
import LoadingSpinner from '../../common/LoadingSpinner';
import TrashIcon from '../../icons/TrashIcon';
import { AddonCategoryType } from '../../../constants';

const AdditionalProductSelectorStep: React.FC = () => {
    const { 
        catalogContext, 
        toggleAdditionalProduct, 
        updateProductQuantity, 
        goToStep,
        isLoading: contextLoading,
        error: contextError,
        dispatch 
    } = useQuoteProcess();
    const { activeQuoteFull } = catalogContext;

    const [additionalProducts, setAdditionalProducts] = useState<ProductPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        apiClient.listCategories(AddonCategoryType) // First, get the "Project Add-ons" category details
            .then(categories => {
                if (categories.length > 0) {
                    // Assuming the first category of type "additional" is the one we want
                    return apiClient.listProductsInCategory(categories[0].name); 
                }
                return [];
            })
            .then(data => setAdditionalProducts(data))
            .catch(err => {
                setError((err as Error).message);
                dispatch({type: 'SET_ERROR', payload: (err as Error).message});
            })
            .finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Debounced quantity update
    const debouncedUpdateQuantity = useCallback(
        debounce((entryId: number, quantity: number) => {
            updateProductQuantity(entryId, quantity);
        }, 500),
        [updateProductQuantity]
    );

    const currentLoading = isLoading || contextLoading;
    const currentError = error || contextError;

    if (currentLoading) return <LoadingSpinner />;
    if (currentError && !additionalProducts.length) return <div className="text-red-500 p-4 bg-red-50 rounded-md">Error: {currentError}</div>;

    return (
        <div className="fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Select Additional Services</h2>
            <p className="text-slate-600 mb-6">Choose any extra services needed for this project (e.g., teardown, hard digging).</p>
            
            {additionalProducts.length > 0 ? (
                <div className="space-y-4">
                    {additionalProducts.map(p => {
                        const entry = activeQuoteFull?.product_entries.find(e => e.product_id === p.id && e.role === ProductRole.ADDITIONAL);
                        const isSelected = !!entry;
                        return (
                            <div key={p.id} className="bg-white p-4 rounded-lg shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                <div className="flex-grow">
                                    <h3 className="font-bold text-slate-800">{p.name}</h3>
                                    <p className="text-sm text-slate-500">{p.description}</p>
                                </div>
                                <div className="flex items-center gap-3 shrink-0 w-full sm:w-auto">
                                    {isSelected && entry ? (
                                        <>
                                            <input 
                                                type="number" 
                                                defaultValue={entry.quantity_of_product_units} // Changed from entry.quantity
                                                onChange={(e) => debouncedUpdateQuantity(entry.id, parseFloat(e.target.value) || 0)}
                                                className="w-20 p-2 border border-slate-300 rounded-md shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500"
                                                aria-label={`Quantity for ${p.name}`}
                                            />
                                            <button 
                                                onClick={() => toggleAdditionalProduct(p.id)} 
                                                className="text-red-500 hover:text-red-700 p-2 rounded-md hover:bg-red-50"
                                                aria-label={`Remove ${p.name}`}
                                            >
                                                <TrashIcon />
                                            </button>
                                        </>
                                    ) : (
                                        <button 
                                            onClick={() => toggleAdditionalProduct(p.id)} 
                                            className="bg-green-100 text-green-700 font-semibold py-2 px-4 rounded-lg hover:bg-green-200 transition-colors text-sm"
                                        >
                                            Add
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                 <p className="text-slate-500">No additional services found.</p>
            )}

            <div className="mt-8 border-t pt-6 flex justify-end">
                <button 
                    onClick={() => goToStep('review')}
                    className="bg-blue-600 text-white font-semibold py-2 px-5 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
                >
                    Next: Review Quote
                </button>
            </div>
        </div>
    );
};

function debounce<T extends (...args: any[]) => any>(func: T, delay: number): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return function(this: ThisParameterType<T>, ...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

export default AdditionalProductSelectorStep;