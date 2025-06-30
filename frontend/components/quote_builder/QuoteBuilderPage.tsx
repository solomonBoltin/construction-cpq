import React, { useEffect } from 'react';
import { useQuoteBuilderStore } from '../../stores/useQuoteBuilderStore';
import { useNavigate, useParams, Navigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import Stepper from './Stepper';
import StepContentRenderer from './StepContentRenderer';
import ChevronLeftIcon from '../icons/ChevronLeftIcon';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const QuoteBuilderPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { quote, loadQuote, isLoading, error, reset } = useQuoteBuilderStore();
    const navigate = useNavigate();

    useEffect(() => {
        // Reset the store when component mounts (ensures clean state)
        reset();
        
        if (id) {
            const quoteId = parseInt(id);
            if (!isNaN(quoteId)) {
                loadQuote(quoteId);
            }
        }

        // Cleanup: reset store when component unmounts
        return () => {
            reset();
        };
    }, [id, loadQuote, reset]);

    if (!id || isNaN(parseInt(id))) {
        return <Navigate to="/" replace />;
    }

    if (isLoading) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-slate-100 p-4">
                <LoadingSpinner />
                <p className="mt-4 text-slate-600">Loading quote details...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-slate-100 p-4">
                <ErrorMessage error={error} className="max-w-md" />
                <button 
                    onClick={() => navigate('/')}
                    className="mt-4 text-blue-600 hover:text-blue-800 underline"
                >
                    Back to quotes
                </button>
            </div>
        );
    }

    if (!quote) {
        return null; // This shouldn't happen, but prevents render errors
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

export default QuoteBuilderPage;
