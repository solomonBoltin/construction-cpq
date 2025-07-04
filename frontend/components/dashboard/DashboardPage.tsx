import React, { useEffect, useState } from 'react';
import { apiClient } from '../../services/api';
import QuoteCard from './QuoteCard';
import PlusIcon from '../icons/PlusIcon';
import LoadingSpinner from '../common/LoadingSpinner';
import Modal from '../common/Modal';
import { QuoteType, QuotePreview } from '../../types';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../stores/useToastStore';
import { handleApiError } from '../../utils/errors';

const DashboardPage: React.FC = () => {
  const [quotes, setQuotes] = useState<QuotePreview[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newQuoteName, setNewQuoteName] = useState('');
  const [newQuoteDescription, setNewQuoteDescription] = useState('');
  const navigate = useNavigate();
  const toast = useToast();

  const fetchQuotes = async () => {
    setIsLoading(true);
    try {
      const quotesData = await apiClient.listQuotes(QuoteType.FENCE_PROJECT);
      setQuotes(quotesData);
    } catch (err) {
      const errorMessage = handleApiError(err);
      toast.error('Failed to load quotes', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const createNewQuote = async (name: string, description: string, type: QuoteType = QuoteType.FENCE_PROJECT) => {
    setIsLoading(true);
    try {
      const newQuote = await apiClient.createQuote(name, type, description);
      await fetchQuotes(); // Refresh the list
      setIsModalOpen(false);
      setNewQuoteName('');
      setNewQuoteDescription('');
      toast.success('Quote created successfully');
      navigate(`/quote/${newQuote.id}`);
      return newQuote.id;
    } catch (err) {
      const errorMessage = handleApiError(err);
      toast.error('Failed to create quote', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateQuote = async () => {
    if (newQuoteName.trim()) {
      const newId = await createNewQuote(newQuoteName.trim(), newQuoteDescription.trim(), QuoteType.FENCE_PROJECT);
      setNewQuoteName('');
      setNewQuoteDescription('');
      if (newId) navigate(`/quote/${newId}`);
    }
  };

  const handleSelectQuote = (quoteId: number) => {
    navigate(`/quote/${quoteId}`);
  };

  if (isLoading && quotes.length === 0) {
    return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>;
  }

  return (
    <div className="min-h-screen bg-slate-100 p-4 sm:p-6 lg:p-8 fade-in">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-slate-800">Fence Projects</h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <PlusIcon />
            New Project
          </button>
        </div>

        {quotes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quotes.map((quote) => (
              <QuoteCard key={quote.id} quote={quote} onSelect={handleSelectQuote} />
            ))}
          </div>
        ) : (
          !isLoading && <p className="text-slate-600 text-center py-10">No projects found. Create one to get started!</p>
        )}
         {isLoading && quotes.length > 0 && <div className="mt-6"><LoadingSpinner /></div>}
      </div>

      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        title="Create New Project"
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="quoteName" className="block text-sm font-medium text-slate-700 mb-1">
              Project Name
            </label>
            <input
              type="text"
              id="quoteName"
              value={newQuoteName}
              onChange={(e) => setNewQuoteName(e.target.value)}
              placeholder="e.g., Johnson Residence Fence"
              className="w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="quoteDescription" className="block text-sm font-medium text-slate-700 mb-1">
              Project Description
            </label>
            <textarea
              id="quoteDescription"
              value={newQuoteDescription}
              onChange={(e) => setNewQuoteDescription(e.target.value)}
              placeholder="e.g., Backyard fence project with a gate"
              rows={3}
              className="w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateQuote}
              disabled={!newQuoteName.trim() || isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage;

