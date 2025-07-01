import React from 'react';
import { useQuoteBuilderStore } from '../../../stores/useQuoteBuilderStore';
import LoadingSpinner from '../../common/LoadingSpinner';
import { ComponentErrorBoundary } from '../../common/ErrorBoundary';
import { useToast } from '../../../stores/useToastStore';
import { handleApiError } from '../../../utils/errors';

const ReviewStepContent: React.FC = () => {
    const { 
        quote, 
        calculatedQuote, 
        calculateQuote,
        finalizeQuote,
        isLoading
    } = useQuoteBuilderStore();
    const toast = useToast();

    // Don't auto-calculate - let the user manually trigger calculation
    const handleCalculateQuote = async () => {
        if (quote && !isLoading) {
            try {
                await calculateQuote();
                toast.success('Quote calculated successfully');
            } catch (err) {
                const errorMessage = handleApiError(err);
                toast.error('Failed to calculate quote', errorMessage);
            }
        }
    };

    const handleFinalizeQuote = async () => {
        if (quote && calculatedQuote && !isLoading) {
            try {
                await finalizeQuote();
                toast.success('Quote finalized successfully! The quote is now read-only.');
            } catch (err) {
                const errorMessage = handleApiError(err);
                toast.error('Failed to finalize quote', errorMessage);
            }
        }
    };

    if (!quote) {
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
            <div className="flex items-center justify-between mb-1">
                <h2 className="text-2xl font-bold text-slate-800">Quote Review</h2>
                {quote?.status === 'FINAL' && (
                    <span className="bg-green-100 text-green-800 text-sm font-medium px-3 py-1 rounded-full">
                        Finalized
                    </span>
                )}
            </div>
            <p className="text-slate-600 mb-6">
                {quote?.status === 'FINAL' 
                    ? 'This quote has been finalized and is read-only.'
                    : 'Review the project items and calculated estimate.'}
            </p>

            <div className="bg-white p-6 sm:p-8 rounded-lg shadow-md max-w-2xl mx-auto">
                <h3 className="text-xl font-bold text-slate-800 mb-6 text-center">
                    {quote.name || "Project"} - Estimate
                </h3>
                
                <div className="space-y-2 mb-6">
                    <h4 className="font-semibold text-slate-700 mb-3 border-b pb-2">Project Items:</h4>
                    {quote.product_entries.length > 0 ? (
                        quote.product_entries.map(entry => (
                            <div key={entry.id} className="text-sm text-slate-600 py-1 flex justify-between">
                                <span>{entry.quantity_of_product_units} x Product ID {entry.product_id}</span> 
                                <span className="italic capitalize">({entry.role?.toString().toLowerCase() || 'unknown'})</span>
                            </div>
                        ))
                    ) : (
                        <p className="text-sm text-slate-500 italic">No items added to this quote yet.</p>
                    )}
                </div>

                <hr className="my-6" />

                {isLoading && <div className="py-4"><LoadingSpinner /></div>}

                {calculatedQuote ? (
                    <>
                        <div className="space-y-2">
                            {renderSummaryItem("Total Material Cost", `$${calculatedQuote.total_material_cost}`)}
                            {renderSummaryItem("Total Labor Cost", `$${calculatedQuote.total_labor_cost}`)}
                            {calculatedQuote.cost_of_goods_sold && renderSummaryItem("Cost of Goods Sold", `$${calculatedQuote.cost_of_goods_sold}`)}
                            {calculatedQuote.applied_rates_info_json?.map((rate, index) => 
                                <div key={rate.name || index}>
                                    {renderSummaryItem(rate.name, `$${rate.applied_amount} (${(parseFloat(rate.rate_value)*100).toFixed(1)}%)`)}
                                </div>
                            )}
                             <div className="pt-2">
                                {renderSummaryItem("Subtotal Before Tax", `$${calculatedQuote.subtotal_before_tax}`, true)}
                             </div>
                            {renderSummaryItem("Tax Amount", `$${calculatedQuote.tax_amount}`)}
                        </div>
                        <hr className="my-4 border-slate-300" />
                        <div className="flex justify-between font-bold text-2xl text-slate-900 mt-2 mb-1">
                            <span>Final Price</span>
                            <span>${calculatedQuote.final_price}</span>
                        </div>
                         <p className="text-xs text-slate-400 mt-2 text-center">Calculated at: {new Date(calculatedQuote.calculated_at).toLocaleString()}</p>
                    </>
                ) : (
                    !isLoading && (
                        <div className="text-center py-6">
                            <p className="text-slate-500 mb-4">Estimate not yet calculated for this version of the quote.</p>
                            <button 
                                onClick={handleCalculateQuote}
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
                    onClick={handleFinalizeQuote}
                    disabled={!calculatedQuote || isLoading || quote?.status === 'FINAL'}
                    className="bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                   >
                     {quote?.status === 'FINAL' 
                       ? 'Project Finalized' 
                       : isLoading 
                         ? 'Finalizing...' 
                         : 'Finalize Project'}
                    </button>
                    {quote?.status === 'FINAL' && (
                      <p className="text-sm text-green-600 mt-2 font-medium">
                        This quote has been finalized and is now read-only.
                      </p>
                    )}
                </div>
            </div>
        </div>
    );
};

const ReviewStep: React.FC = () => (
    <ComponentErrorBoundary>
        <ReviewStepContent />
    </ComponentErrorBoundary>
);

export default ReviewStep;