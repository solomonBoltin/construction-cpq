import React, { useEffect } from 'react';
import { useQuoteProcess } from '../../../contexts/QuoteProcessContext';
import LoadingSpinner from '../../common/LoadingSpinner';

const ReviewStep: React.FC = () => {
    const { 
        activeQuoteId, 
        catalogContext, 
        calculatedQuoteResult, 
        calculateActiveQuote,
        fetchCalculatedQuote,
        isLoading, 
        error 
    } = useQuoteProcess();
    const { activeQuoteFull } = catalogContext;

    useEffect(() => {
        if (activeQuoteId) {
            // Check if we already have a result or try to fetch/calculate
            if (!calculatedQuoteResult) {
                 fetchCalculatedQuote(activeQuoteId); // Try to fetch existing first
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeQuoteId]);
    
    // Fallback if fetchCalculatedQuote doesn't find anything and we need to trigger calculation
    const handleCalculateIfNeeded = () => {
        if (activeQuoteId && !calculatedQuoteResult && !isLoading) {
            calculateActiveQuote();
        }
    }

    if (!activeQuoteFull) {
        return <div className="p-4 text-slate-500">Loading quote information...</div>;
    }

    const renderSummaryItem = (label: string, value: string | number, isBold: boolean = false) => (
        <div className={`flex justify-between py-1 ${isBold ? 'font-semibold text-slate-800' : 'text-slate-600'}`}>
            <span>{label}</span>
            <span>{value}</span>
        </div>
    );
    
    return (
        <div className="fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Quote Review</h2>
            <p className="text-slate-600 mb-6">Review the project items and calculated estimate.</p>

            <div className="bg-white p-6 sm:p-8 rounded-lg shadow-md max-w-2xl mx-auto">
                <h3 className="text-xl font-bold text-slate-800 mb-6 text-center">
                    {activeQuoteFull.name || "Project"} - Estimate
                </h3>
                
                <div className="space-y-2 mb-6">
                    <h4 className="font-semibold text-slate-700 mb-3 border-b pb-2">Project Items:</h4>
                    {activeQuoteFull.product_entries.length > 0 ? (
                        activeQuoteFull.product_entries.map(entry => (
                            <div key={entry.id} className="text-sm text-slate-600 py-1 flex justify-between">
                                <span>{entry.quantity_of_product_units} x Product ID {entry.product_id}</span> 
                                <span className="italic capitalize">({entry.role.toString().toLowerCase()})</span>
                            </div>
                        ))
                    ) : (
                        <p className="text-sm text-slate-500 italic">No items added to this quote yet.</p>
                    )}
                </div>

                <hr className="my-6" />

                {isLoading && <div className="py-4"><LoadingSpinner /></div>}
                {error && <div className="text-red-500 p-3 bg-red-100 rounded text-sm mb-4">Error: {error}</div>}

                {calculatedQuoteResult ? (
                    <>
                        <div className="space-y-2">
                            {renderSummaryItem("Total Material Cost", `$${calculatedQuoteResult.total_material_cost}`)}
                            {renderSummaryItem("Total Labor Cost", `$${calculatedQuoteResult.total_labor_cost}`)}
                            {calculatedQuoteResult.cost_of_goods_sold && renderSummaryItem("Cost of Goods Sold", `$${calculatedQuoteResult.cost_of_goods_sold}`)}
                            {calculatedQuoteResult.applied_rates_info_json?.map(rate => 
                                renderSummaryItem(rate.name, `$${rate.applied_amount} (${(parseFloat(rate.rate_value)*100).toFixed(1)}%)`)
                            )}
                             <div className="pt-2">
                                {renderSummaryItem("Subtotal Before Tax", `$${calculatedQuoteResult.subtotal_before_tax}`, true)}
                             </div>
                            {renderSummaryItem("Tax Amount", `$${calculatedQuoteResult.tax_amount}`)}
                        </div>
                        <hr className="my-4 border-slate-300" />
                        <div className="flex justify-between font-bold text-2xl text-slate-900 mt-2 mb-1">
                            <span>Final Price</span>
                            <span>${calculatedQuoteResult.final_price}</span>
                        </div>
                         <p className="text-xs text-slate-400 mt-2 text-center">Calculated at: {new Date(calculatedQuoteResult.calculated_at).toLocaleString()}</p>
                    </>
                ) : (
                    !isLoading && (
                        <div className="text-center py-6">
                            <p className="text-slate-500 mb-4">Estimate not yet calculated for this version of the quote.</p>
                            <button 
                                onClick={handleCalculateIfNeeded}
                                disabled={isLoading}
                                className="bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                            >
                                {isLoading ? 'Calculating...' : 'Calculate Estimate'}
                            </button>
                        </div>
                    )
                )}
                
                <div className="mt-8 text-center">
                   <button 
                    disabled={!calculatedQuoteResult || isLoading}
                    className="bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                   >
                     Finalize Project (Not Implemented)
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ReviewStep;