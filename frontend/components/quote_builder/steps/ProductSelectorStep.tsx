import React, { useEffect, useState } from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import { useStepNavigation } from '../../../hooks/useStepNavigation';
import { useProductConfirmation, needsProductConfirmation } from '../../../hooks/useProductConfirmation';
import { apiClient } from '../../../services/api';
import { ProductPreview, ProductRole, CategoryPreview } from '../../../types';
import { GateCategoryType } from '../../../constants';
import GenericProductSelector from '../GenericProductSelector';
import Modal from '../../common/Modal';

interface ProductSelectorStepProps {
    role: ProductRole.MAIN | ProductRole.SECONDARY;
}

const ProductSelectorStep: React.FC<ProductSelectorStepProps> = ({ role }) => {
    const { 
        selectProduct, 
        selectedCategoryName,
        quote,
        removeEntry,
        isLoading: contextLoading, 
        error: contextError
    } = useQuoteBuilderStore();
    const { navigateAfterAction, goToStep } = useStepNavigation();
    const { isConfirmationOpen, confirmationMessage, showConfirmation, closeConfirmation, confirmAction } = useProductConfirmation();

    const [products, setProducts] = useState<ProductPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const title = role === ProductRole.MAIN ? 'Select Main Fence Product' : 'Select Gate Product';

    useEffect(() => {
        const fetchProducts = async () => {
            setIsLoading(true);
            setError(null);
            try {
                let data: ProductPreview[] = [];
                if (role === ProductRole.MAIN) {
                    if (!selectedCategoryName) throw new Error("Please select a category first.");
                    data = await apiClient.listProductsInCategory(selectedCategoryName);
                } else if (role === ProductRole.SECONDARY) {
                    data = await apiClient.listProductsByCategoryType(GateCategoryType);
                }
                setProducts(data);
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchProducts();
    }, [selectedCategoryName, role]);

    const handleSelectProduct = async (item: ProductPreview | CategoryPreview) => {
        // Type guard to ensure it's a ProductPreview
        if ('id' in item && typeof item.id === 'number') {
            // Check if confirmation is needed
            const confirmation = needsProductConfirmation(role, quote?.product_entries || []);
            
            if (confirmation.needed) {
                const confirmed = await showConfirmation(confirmation.message);
                
                if (!confirmed) {
                    return;
                }
                
                // Remove existing entry before adding new one
                const existingEntry = quote?.product_entries?.find(e => e.role === role);
                if (existingEntry) {
                    await removeEntry(existingEntry.id);
                }
            }

            try {
                const productEntry = await selectProduct(item.id, role);
                // Navigate immediately after successful product selection
                if (productEntry) {
                    navigateAfterAction('productSelected', role);
                }
            } catch (error) {
                // Error is handled by the store
            }
        }
    };

    // If it's a main product step and no category is selected, show error
    if (role === ProductRole.MAIN && !selectedCategoryName) {
        return (
            <div className="text-center p-8 bg-white rounded-lg shadow">
                <h3 className="font-bold text-lg text-slate-700">Please select a category first.</h3>
                <button 
                    onClick={() => goToStep('choose_category')} 
                    className="mt-4 bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
                >
                    Go to Category Selection
                </button>
            </div>
        );
    }

    const currentEntryForRole = quote?.product_entries?.find(e => e.role === role);
    const selectedProduct = products.find(p => p.id === currentEntryForRole?.product_id);

    return (
        <>
            <div className="fade-in">
                <GenericProductSelector
                    title={title}
                    items={products}
                    isLoading={isLoading || contextLoading}
                    error={error || contextError}
                    onSelect={handleSelectProduct}
                    selectedId={selectedProduct?.id}
                    emptyMessage={`No ${role === ProductRole.MAIN ? 'fence' : 'gate'} products available.`}
                />
            </div>

            <Modal
                isOpen={isConfirmationOpen}
                onClose={closeConfirmation}
                title="Replace Product?"
            >
                <div className="space-y-4">
                    <p className="text-slate-600">{confirmationMessage}</p>
                    <div className="flex gap-3 justify-end">
                        <button
                            onClick={closeConfirmation}
                            className="px-4 py-2 text-slate-600 hover:text-slate-800 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={confirmAction}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Replace Product
                        </button>
                    </div>
                </div>
            </Modal>
        </>
    );
};

export default ProductSelectorStep;

