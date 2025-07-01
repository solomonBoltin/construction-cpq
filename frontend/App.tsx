import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardPage from './components/dashboard/DashboardPage';
import QuoteBuilderPage from './components/quote_builder/QuoteBuilderPage';
import { AppErrorBoundary, PageErrorBoundary } from './components/common/ErrorBoundary';
import { ToastContainer } from './components/common/Toast';

const App: React.FC = () => {
  return (
    <AppErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={
            <PageErrorBoundary>
              <DashboardPage />
            </PageErrorBoundary>
          } />
          <Route path="/quote/:id" element={
            <PageErrorBoundary>
              <QuoteBuilderPage />
            </PageErrorBoundary>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <ToastContainer />
    </AppErrorBoundary>
  );
};

export default App;
