import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QuoteProcessProvider } from './contexts/QuoteProcessContext';
import QuoteListPage from './components/quote_list/QuoteListPage';
import QuoteCatalogRoute from './components/QuoteCatalogRoute';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <QuoteProcessProvider>
        <Routes>
          <Route path="/" element={<QuoteListPage />} />
          <Route path="/quote/:id" element={<QuoteCatalogRoute />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </QuoteProcessProvider>
    </BrowserRouter>
  );
};

export default App;
