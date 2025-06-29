import React, { useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useQuoteProcess } from '../contexts/QuoteProcessContext';
import CatalogPage from './catalog/CatalogPage';
import LoadingSpinner from './common/LoadingSpinner';

const QuoteCatalogRoute: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { activeQuoteId, selectQuoteForEditing, catalogContext, isLoading } = useQuoteProcess();

  useEffect(() => {
    if (id && parseInt(id) !== activeQuoteId) {
      selectQuoteForEditing(parseInt(id));
    }
  }, [id, activeQuoteId, selectQuoteForEditing]);

  if (!id || isNaN(parseInt(id))) {
    return <Navigate to="/" replace />;
  }

  if (isLoading && !catalogContext.activeQuoteFull) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return <CatalogPage />;
};

export default QuoteCatalogRoute;
