import React from 'react';
import { useQuoteProcess } from '../../contexts/QuoteProcessContext';
import { ProductRole } from '../../types';
import ChevronRightIcon from '../icons/ChevronRightIcon';
import { MOCKUP_DEFAULT_IMAGE } from '../../constants';

const Sidebar: React.FC = () => {
    const { catalogContext, goToStep } = useQuoteProcess();
    const { activeQuoteFull } = catalogContext;

    if (!activeQuoteFull) {
        return (
            <aside className="w-80 bg-slate-50 border-r border-slate-200 flex flex-col h-full p-6">
                <p className="text-slate-500">Loading quote details...</p>
            </aside>
        );
    }
    
    // In a real app with full product data, we'd look up names. Using IDs for now for mock.
    const getProductName = (productId: number): string => {
        // This is a placeholder. Real app would fetch product details or have them available.
        // For the mock, we can try to find it in the 'apiClient's product list if needed, or just use ID.
        // For simplicity with current mock structure:
        return `Product ID ${productId}`; 
    };

    const product_entries = activeQuoteFull.product_entries || [];
    const mainProduct = product_entries.find(e => e.role === ProductRole.MAIN);
    const secondaryProduct = product_entries.find(e => e.role === ProductRole.SECONDARY);
    const additionalProducts = product_entries.filter(e => e.role === ProductRole.ADDITIONAL);

    return (
        <aside className="w-80 bg-slate-50 border-r border-slate-200 flex flex-col h-full">
            <div className="p-6 border-b border-slate-200">
                <h2 className="text-lg font-bold text-slate-800 truncate" title={activeQuoteFull.name || "Unnamed Quote"}>
                    {activeQuoteFull.name || "Unnamed Quote"}
                </h2>
                <p className="text-sm text-slate-500 truncate" title={activeQuoteFull.description || ""}>
                    {activeQuoteFull.description || "No description."}
                </p>
            </div>
            <div className="flex-1 p-6 overflow-y-auto">
                <h3 className="font-semibold text-slate-700 mb-4">Project Items</h3>
                <ul className="space-y-4 text-sm">
                    <li>
                        <span className={`font-semibold block ${mainProduct ? 'text-slate-600' : 'text-slate-400'}`}>Main Product</span>
                        {mainProduct ? (
                             <span className="text-slate-500">{activeQuoteFull.product_entries.find(pe => pe.id === mainProduct.id)?.product_id ? `Configured Item` : `Select Item`}</span>
                        ) : (
                            <span className="text-slate-400 italic">Not selected</span>
                        )}
                    </li>
                    <li>
                        <span className={`font-semibold block ${secondaryProduct ? 'text-slate-600' : 'text-slate-400'}`}>Secondary Product</span>
                         {secondaryProduct ? (
                             <span className="text-slate-500">{activeQuoteFull.product_entries.find(pe => pe.id === secondaryProduct.id)?.product_id ? `Configured Item` : `Select Item`}</span>
                        ) : (
                            <span className="text-slate-400 italic">Not selected</span>
                        )}
                    </li>
                    {additionalProducts.length > 0 && (
                        <li>
                            <span className="font-semibold text-slate-600 block">Additional Items</span>
                            <ul className="list-disc list-inside mt-1 text-slate-500">
                                {additionalProducts.map(p => <li key={p.id}>{getProductName(p.product_id)}</li>)}
                            </ul>
                        </li>
                    )}
                </ul>
            </div>
            <div className="p-6 border-t border-slate-200">
                <button 
                    onClick={() => goToStep('review')}
                    className="w-full bg-green-600 text-white font-semibold py-3 px-4 rounded-lg shadow-md hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                >
                    Review & Calculate
                    <ChevronRightIcon />
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
