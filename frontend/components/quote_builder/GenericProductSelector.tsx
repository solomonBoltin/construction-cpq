import React from 'react';
import { ProductPreview, CategoryPreview } from '../../types';
import ProductDisplayCard from './ProductDisplayCard';
import LoadingSpinner from '../common/LoadingSpinner';
import { ComponentErrorBoundary } from '../common/ErrorBoundary';

interface GenericProductSelectorProps {
  title: string;
  items: (ProductPreview | CategoryPreview)[];
  isLoading: boolean;
  error?: string | null; // Make optional since we're using toast-based error handling
  onSelect: (item: ProductPreview | CategoryPreview) => void;
  selectedId?: number;
  emptyMessage?: string;
}

const GenericProductSelectorContent: React.FC<GenericProductSelectorProps> = ({
  title,
  items,
  isLoading,
  onSelect,
  selectedId,
  emptyMessage = "No items available."
}) => {
  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      <h2 className="text-2xl font-bold text-slate-800 mb-6">{title}</h2>
      
      {items.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <ProductDisplayCard
              key={item.id || item.name}
              item={item}
              isSelected={selectedId === item.id}
              onSelect={() => onSelect(item)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-slate-400 text-lg">{emptyMessage}</div>
        </div>
      )}
    </div>
  );
};

const GenericProductSelector: React.FC<GenericProductSelectorProps> = (props) => (
  <ComponentErrorBoundary>
    <GenericProductSelectorContent {...props} />
  </ComponentErrorBoundary>
);

export default GenericProductSelector;
