import React, { useEffect } from 'react';
import { useQuoteProcess } from '../../contexts/QuoteProcessContext';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import Stepper from './Stepper';
import StepContentRenderer from './StepContentRenderer';
import ChevronLeftIcon from '../icons/ChevronLeftIcon';
import LoadingSpinner from '../common/LoadingSpinner';

const CatalogPage: React.FC = () => {
    const { activeQuoteId, catalogContext } = useQuoteProcess();
    const navigate = useNavigate();

    useEffect(() => {
        // This ensures that if catalog page is loaded directly (e.g. refresh)
        // and activeQuoteFull is not set, we try to load it.
        // selectQuoteForEditing handles this, called when a quote is selected from list.
        // This is a safety net.
        if (activeQuoteId && !catalogContext.activeQuoteFull) {
            // Consider calling a function here that re-fetches the activeQuoteFull
            // e.g. from useQuoteProcess context:  loadActiveQuoteDetails(activeQuoteId);
            // For now, this scenario implies an issue with state persistence or flow.
            console.warn("CatalogPage loaded with activeQuoteId but no activeQuoteFull details. State might be inconsistent.");
        }
    }, [activeQuoteId, catalogContext.activeQuoteFull]);


    if (!activeQuoteId || !catalogContext.activeQuoteFull) {
        // This can happen if navigating directly or state is lost.
        // A robust app would handle this by redirecting or attempting to load.
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-slate-100 p-4">
                 <LoadingSpinner />
                <p className="mt-4 text-slate-600">Loading quote details...</p>
                 <button 
                    onClick={() => navigate('/')} // Use router navigation
                    className="mt-6 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                    <ChevronLeftIcon />
                    Back to All Projects
                </button>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-white">
            <Sidebar />
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="p-4 border-b border-slate-200 bg-white z-10">
                    <button 
                        onClick={() => navigate('/')} // Use router navigation
                        className="text-sm text-slate-600 hover:text-blue-600 flex items-center gap-1"
                    >
                        <ChevronLeftIcon />
                        Back to All Projects
                    </button>
                </header>
                
                <div className="p-4 sm:p-6 border-b border-slate-200">
                     <Stepper />
                </div>

                <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-100">
                    <StepContentRenderer />
                </div>
            </main>
        </div>
    );
};

export default CatalogPage;
