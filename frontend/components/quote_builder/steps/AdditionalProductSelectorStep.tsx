import React, { useEffect, useState } from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import { useStepNavigation } from '../../../hooks/useStepNavigation';
import { apiClient } from '../../../services/api';
import { ProductPreview, ProductRole, CategoryPreview } from '../../../types';
import { AddonCategoryType } from '../../../constants';
import GenericProductSelector from '../GenericProductSelector';
import TrashIcon from '../../icons/TrashIcon';

const AdditionalProductSelectorStep: React.FC = () => {
    const { 
        quote, 
        selectProduct, 
        removeEntry,
        isLoading: contextLoading,
        error: contextError
    } = useQuoteBuilderStore();
    const { goToStep } = useStepNavigation();

    const [additionalProducts, setAdditionalProducts] = useState<ProductPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProducts = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const categories = await apiClient.listCategories(AddonCategoryType);
                if (categories.length > 0) {
                    const products = await apiClient.listProductsInCategory(categories[0].name);
                    setAdditionalProducts(products);
                } else {
                    setAdditionalProducts([]);
                }
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchProducts();
    }, []);

    const handleSelectProduct = (item: ProductPreview | CategoryPreview) => {
        // Type guard to ensure it's a ProductPreview
        if ('id' in item && typeof item.id === 'number') {
            selectProduct(item.id, ProductRole.ADDITIONAL);
        }
    };

    const selectedAdditionalProducts = quote?.product_entries?.filter(e => e.role === ProductRole.ADDITIONAL) || [];

    return (
        <div className="fade-in">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Additional Services</h2>
                <p className="text-slate-600">
                    Select any additional services like teardown, hard digging, or cleanup that you'd like to include in this quote.
                </p>
            </div>

            {selectedAdditionalProducts.length > 0 && (
                <div className="mb-8 p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-semibold text-slate-800 mb-3">Selected Additional Services:</h3>
                    <div className="space-y-2">
                        {selectedAdditionalProducts.map(product => (
                            <div key={product.id} className="flex items-center justify-between bg-white p-3 rounded border">
                                <div className="flex-1">
                                    <span className="font-medium text-slate-800">{product.product_name}</span>
                                    <span className="text-sm text-slate-600 ml-2">(Qty: {product.quantity_of_product_units})</span>
                                </div>
                                <button
                                    onClick={() => removeEntry(product.id)}
                                    className="text-red-500 hover:text-red-700 p-1"
                                    title="Remove service"
                                >
                                    <TrashIcon className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <GenericProductSelector
                title="Available Additional Services"
                items={additionalProducts}
                isLoading={isLoading || contextLoading}
                error={error || contextError}
                onSelect={handleSelectProduct}
                emptyMessage="No additional services available."
            />

            <div className="mt-8 space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-600">
                        <strong>Note:</strong> You can select multiple additional services. Each service will be added to your quote as a separate line item.
                    </p>
                </div>

                <div className="flex justify-between">
                    <button
                        onClick={() => goToStep('configure_secondary')}
                        className="px-4 py-2 text-slate-600 hover:text-slate-800"
                    >
                        ← Back
                    </button>
                    <button
                        onClick={() => goToStep('review')}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Continue to Review →
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AdditionalProductSelectorStep;
