import React from 'react';
import { useQuoteProcess } from '../../contexts/QuoteProcessContext';
import { MaterializedProductEntry, ProductRole } from '../../types';
import ChevronRightIcon from '../icons/ChevronRightIcon';
import { MOCKUP_DEFAULT_IMAGE } from '../../constants';
import { shortUnitType } from '@/utils/units';

const Sidebar: React.FC = () => {
    const { catalogContext, goToStep } = useQuoteProcess();
    const { activeQuoteFull } = catalogContext;

    console.log("Sidebar data:", activeQuoteFull);

    if (!activeQuoteFull) {
        return (
            <aside className="w-80 bg-slate-50 border-r border-slate-200 flex flex-col h-full p-6">
                <p className="text-slate-500">Loading quote details...</p>
            </aside>
        );
    }

    const product_entries = activeQuoteFull.product_entries || [];
    const mainProduct = product_entries.find(e => e.role === ProductRole.MAIN);
    const secondaryProduct = product_entries.find(e => e.role === ProductRole.SECONDARY);
    const additionalProducts = product_entries.filter(e => e.role === ProductRole.ADDITIONAL);

    // Helper to render product entry details
    const renderProductEntry = (entry: MaterializedProductEntry) => {
        const selectedOptions = entry.variation_groups?.flatMap((g: any) => g.options.filter((o: any) => o.is_selected)) || [];

        return (
            <div className="flex items-start gap-3 p-2 rounded-lg bg-white shadow-sm border border-slate-100 mb-2">
                <img
                    src={entry.product_image_url || MOCKUP_DEFAULT_IMAGE}
                    alt={entry.product_name || 'Product'}
                    className="w-12 h-12 object-cover rounded-md border border-slate-200"
                />
                <div className="flex-1 min-w-0">
                    <div className="font-medium text-xs text-slate-700 truncate" title={entry.product_name}>
                        {entry.quantity_of_product_units} {shortUnitType(entry.product_unit)} of {entry.product_name || `Product #${entry.product_id}`}
                    </div>
                    {selectedOptions.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                            {selectedOptions.map((v: any) => (
                                <span key={v.id} className="bg-green-100 text-green-800 text-[11px] font-medium px-2 py-0.5 rounded-full">
                                    {v.name}
                                </span>
                            ))}
                        </div>
                    )}
                    {entry.notes && <div className="mt-1 text-xs text-slate-400 italic">{entry.notes}</div>}
                </div>
            </div>
        );
    }

    return (
        <aside className="resize-x overflow-auto min-w-56 max-w-xl w-80 bg-slate-50 border-r border-slate-200 flex flex-col h-full">
            <div className="p-6 border-b border-slate-200">
                <h2 className="text-lg font-bold text-slate-800 truncate" title={activeQuoteFull.name || 'Unnamed Quote'}>
                    {activeQuoteFull.name || 'Unnamed Quote'}
                </h2>
                <p className="text-sm text-slate-500 truncate" title={activeQuoteFull.description || ''}>
                    {activeQuoteFull.description || 'No description.'}
                </p>
            </div>
            <div className="flex-1 p-6 overflow-y-auto">
                <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                    <span>Project Items</span>
                    <span className="ml-auto bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium">{product_entries.length} total</span>
                </h3>
                <div className="mb-4">
                    <div className="font-semibold text-slate-600 mb-1">Main Product</div>
                    {mainProduct ? renderProductEntry(mainProduct) : <div className="text-slate-400 italic">Not selected</div>}
                </div>
                <div className="mb-4">
                    <div className="font-semibold text-slate-600 mb-1">Secondary Product</div>
                    {secondaryProduct ? renderProductEntry(secondaryProduct) : <div className="text-slate-400 italic">Not selected</div>}
                </div>
                {additionalProducts.length > 0 && (
                    <div className="mb-2">
                        <div className="font-semibold text-slate-600 mb-1">Additional Items <span className="ml-1 bg-slate-200 text-slate-700 text-xs px-2 py-0.5 rounded-full font-medium">{additionalProducts.length}</span></div>
                        {additionalProducts.map((p, idx) => (
                            <div key={p.id || idx}>{renderProductEntry(p)}</div>
                        ))}
                    </div>
                )}
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
