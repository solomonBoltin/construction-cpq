
import React, { useEffect, useState }from 'react';
import { useQuoteProcess } from '../../../contexts/QuoteProcessContext';
import { apiClient } from '../../../services/api';
import { CategoryPreview } from '../../../types';
import LoadingSpinner from '../../common/LoadingSpinner';
import ProductDisplayCard from '../ProductDisplayCard';
import { FenceCategoryType } from '../../../constants';


const CategorySelectorStep: React.FC = () => {
    const { selectCategory, catalogContext, isLoading: contextLoading, error: contextError, dispatch } = useQuoteProcess();
    const [categories, setCategories] = useState<CategoryPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        const fetchCategories = async () => {
            setIsLoading(true);
            setError(null);
            try {
                // For "Choose Category" step, we usually mean main product category type, e.g., "fence"
                const data = await apiClient.listCategories(FenceCategoryType);
                setCategories(data);
            } catch (err) {
                setError((err as Error).message);
                 dispatch({type: 'SET_ERROR', payload: (err as Error).message});
            } finally {
                setIsLoading(false);
            }
        };
        fetchCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const currentLoading = isLoading || contextLoading;
    const currentError = error || contextError;

    if (currentLoading) return <LoadingSpinner />;
    if (currentError) return <div className="text-red-500 p-4 bg-red-50 rounded-md">Error: {currentError}</div>;

    return (
        <div className="fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Choose a Fence Category</h2>
            <p className="text-slate-600 mb-6">Select the primary type of fence for this project.</p>
            {categories.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {categories.map(cat => (
                        <ProductDisplayCard
                            key={cat.id || cat.name}
                            item={cat}
                            isSelected={catalogContext.selectedCategoryName === cat.name}
                            onSelect={() => selectCategory(cat.name)}
                        />
                    ))}
                </div>
            ) : (
                <p className="text-slate-500">No categories found for '{FenceCategoryType}'.</p>
            )}
        </div>
    );
};

export default CategorySelectorStep;
