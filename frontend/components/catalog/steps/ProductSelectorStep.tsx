import React, { useEffect, useState } from 'react';
import { useQuoteProcess } from '../../../contexts/QuoteProcessContext';
import { apiClient } from '../../../services/api';
import { ProductPreview, ProductRole } from '../../../types';
import LoadingSpinner from '../../common/LoadingSpinner';
import ProductDisplayCard from '../ProductDisplayCard';
import { GateCategoryType, AddonCategoryType, MainProductCategoryType } from '../../../constants';


interface ProductSelectorStepProps {
    role: ProductRole.MAIN | ProductRole.SECONDARY; // Or other roles if generalized
}

const ProductSelectorStep: React.FC<ProductSelectorStepProps> = ({ role }) => {
    const { 
        selectProduct, 
        catalogContext, 
        goToStep, 
        isLoading: contextLoading, 
        error: contextError,
        dispatch
    } = useQuoteProcess();
    const { selectedCategoryName, activeQuoteFull } = catalogContext;

    const [products, setProducts] = useState<ProductPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const categoryForRole = role === ProductRole.MAIN ? selectedCategoryName : GateCategoryType; // Gates for secondary
    const title = role === ProductRole.MAIN ? 'Main Fence' : 'Gate';

    useEffect(() => {
        if (!categoryForRole) {
            if (role === ProductRole.MAIN) {
                 setError("Please select a category first.");
            } else { // Secondary product (gate) doesn't strictly depend on main category selection
                 fetchProducts(GateCategoryType);
            }
            return;
        }
        fetchProducts(categoryForRole);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [categoryForRole, role]);

    const fetchProducts = async (categoryName: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await apiClient.listProductsInCategory(categoryName);
            setProducts(data);
        } catch (err) {
            setError((err as Error).message);
            dispatch({type: 'SET_ERROR', payload: (err as Error).message});
        } finally {
            setIsLoading(false);
        }
    };
    
    const currentLoading = isLoading || contextLoading;
    const currentError = error || contextError;

    if (!categoryForRole && role === ProductRole.MAIN) {
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
    
    if (currentLoading) return <LoadingSpinner />;
    if (currentError && !products.length) return <div className="text-red-500 p-4 bg-red-50 rounded-md">Error: {currentError}</div>;

    const currentEntryForRole = activeQuoteFull?.product_entries?.find(e => e.role === role);

    return (
        <div className="fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Choose a {title}</h2>
            <p className="text-slate-600 mb-6">
                {categoryForRole ? `Showing products from the "${categoryForRole}" category.` : `Select a ${title}.`}
            </p>
            {products.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {products.map(p => (
                        <ProductDisplayCard
                            key={p.id}
                            item={p}
                            isSelected={currentEntryForRole?.product_id === p.id}
                            onSelect={() => selectProduct(p.id, role)}
                        />
                    ))}
                </div>
            ) : (
                 <p className="text-slate-500">No products found for "{categoryForRole}".</p>
            )}
        </div>
    );
};

export default ProductSelectorStep;

