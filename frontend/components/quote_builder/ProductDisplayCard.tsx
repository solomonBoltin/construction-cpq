
import React from 'react';
import { ProductPreview, CategoryPreview } from '../../types';
import { MOCKUP_DEFAULT_IMAGE } from '../../constants';

interface ProductDisplayCardProps {
  item: ProductPreview | CategoryPreview;
  isSelected?: boolean;
  onSelect: () => void;
}

const ProductDisplayCard: React.FC<ProductDisplayCardProps> = ({ item, isSelected, onSelect }) => {
  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-xl shadow-md hover:shadow-xl border-2 transition-all cursor-pointer overflow-hidden
                  ${isSelected ? 'border-blue-500 ring-2 ring-blue-500 ring-offset-1' : 'border-transparent hover:border-blue-300'}`}
    >
      <img
        src={item.image_url || MOCKUP_DEFAULT_IMAGE}
        alt={item.name}
        className="w-full h-48 object-cover"
        onError={(e) => (e.currentTarget.src = MOCKUP_DEFAULT_IMAGE)}
      />
      <div className="p-4">
        <h3 className="font-bold text-lg text-slate-800 truncate" title={item.name}>{item.name}</h3>
        {'description' in item && item.description && (
          <p className="text-sm text-slate-500 h-10 overflow-hidden text-ellipsis">{item.description}</p>
        )}
      </div>
    </div>
  );
};

export default ProductDisplayCard;
