
import React, { useEffect, useState } from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import { useStepNavigation } from '../../../hooks/useStepNavigation';
import { apiClient } from '../../../services/api';
import { CategoryPreview } from '../../../types';
import { FenceCategoryType } from '../../../constants';
import GenericProductSelector from '../GenericProductSelector';

const CategorySelectorStep: React.FC = () => {
    const { selectCategory, selectedCategoryName, isLoading: contextLoading, error: contextError } = useQuoteBuilderStore();
    const { navigateAfterAction } = useStepNavigation();
    const [categories, setCategories] = useState<CategoryPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        const fetchCategories = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const data = await apiClient.listCategories(FenceCategoryType);
                setCategories(data);
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchCategories();
    }, []);

    const handleSelectCategory = (category: CategoryPreview) => {
        selectCategory(category.name);
        navigateAfterAction('categorySelected');
    };

    const selectedCategory = categories.find(cat => cat.name === selectedCategoryName);

    return (
        <div className="fade-in">
            <p className="text-slate-600 mb-6">Select the primary type of fence for this project.</p>
            <GenericProductSelector
                title="Choose a Fence Category"
                items={categories}
                isLoading={isLoading || contextLoading}
                error={error || contextError}
                onSelect={handleSelectCategory}
                selectedId={selectedCategory?.id}
                emptyMessage="No fence categories available."
            />
        </div>
    );
};

export default CategorySelectorStep;
