
import React from 'react';
import { QuoteProcessProvider, useQuoteProcess } from './contexts/QuoteProcessContext';
import QuoteListPage from './components/quote_list/QuoteListPage';
import CatalogPage from './components/catalog/CatalogPage';

const AppContent: React.FC = () => {
  const { currentView } = useQuoteProcess();

  if (currentView === 'catalog') {
    return <CatalogPage />;
  }
  return <QuoteListPage />;
};

const App: React.FC = () => {
  return (
    <QuoteProcessProvider>
      <AppContent />
    </QuoteProcessProvider>
  );
};

export default App;
