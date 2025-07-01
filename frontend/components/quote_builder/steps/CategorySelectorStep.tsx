
import React, { useState } from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import { useStepNavigation } from '../../../hooks/useStepNavigation';
import { apiClient } from '../../../services/api';
import { CategoryPreview } from '../../../types';
import { FenceCategoryType } from '../../../constants';
import GenericProductSelector from '../GenericProductSelector';
import { useToast } from '../../../stores/useToastStore';
import { handleApiError } from '../../../utils/errors';
import { ComponentErrorBoundary } from '../../common/ErrorBoundary';
import { useStepFetch } from '../../../hooks/useStepFetch';

const CategorySelectorStepContent: React.FC = () => {
    const { selectCategory, selectedCategoryName, isLoading: contextLoading } = useQuoteBuilderStore();
    const { navigateAfterAction } = useStepNavigation();
    const toast = useToast();
    const [categories, setCategories] = useState<CategoryPreview[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    
    useStepFetch(async () => {
        setIsLoading(true);
        try {
            const data = await apiClient.listCategories(FenceCategoryType);
            setCategories(data);
        } catch (err) {
            const errorMessage = handleApiError(err);
            toast.error('Failed to load categories', errorMessage);
            setCategories([]);
        } finally {
            setIsLoading(false);
        }
    });

    const handleSelectCategory = (category: CategoryPreview) => {
        selectCategory(category.name);
        toast.success(`${category.name} category selected`);
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
                onSelect={handleSelectCategory}
                selectedId={selectedCategory?.id}
                emptyMessage="No fence categories available."
            />
        </div>
    );
};

const CategorySelectorStep: React.FC = () => (
    <ComponentErrorBoundary>
        <CategorySelectorStepContent />
    </ComponentErrorBoundary>
);

export default CategorySelectorStep;
