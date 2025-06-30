import { useState, useCallback } from 'react';
import { ProductRole } from '../types';
import { PRODUCT_ROLE_CONFIG } from '../config/quoteBuilder';

interface UseProductConfirmationReturn {
  isConfirmationOpen: boolean;
  confirmationMessage: string;
  showConfirmation: (message: string) => Promise<boolean>;
  closeConfirmation: () => void;
  confirmAction: () => void;
}

export const useProductConfirmation = (): UseProductConfirmationReturn => {
  const [isConfirmationOpen, setIsConfirmationOpen] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const [resolvePromise, setResolvePromise] = useState<((value: boolean) => void) | null>(null);

  const showConfirmation = useCallback((message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmationMessage(message);
      setIsConfirmationOpen(true);
      setResolvePromise(() => resolve);
    });
  }, []);

  const closeConfirmation = useCallback(() => {
    setIsConfirmationOpen(false);
    if (resolvePromise) {
      resolvePromise(false);
      setResolvePromise(null);
    }
  }, [resolvePromise]);

  const confirmAction = useCallback(() => {
    setIsConfirmationOpen(false);
    if (resolvePromise) {
      resolvePromise(true);
      setResolvePromise(null);
    }
  }, [resolvePromise]);

  return {
    isConfirmationOpen,
    confirmationMessage,
    showConfirmation,
    closeConfirmation,
    confirmAction,
  };
};

export const needsProductConfirmation = (
  role: ProductRole,
  existingEntries: Array<{ role?: ProductRole | null }>
): { needed: boolean; message: string } => {
  const config = PRODUCT_ROLE_CONFIG[role as keyof typeof PRODUCT_ROLE_CONFIG];
  
  if (!config || !config.requiresConfirmationToReplace || !config.maxCount) {
    return { needed: false, message: '' };
  }

  const existingCount = existingEntries.filter(e => e.role === role).length;
  
  if (existingCount >= config.maxCount) {
    return {
      needed: true,
      message: config.confirmationMessage || `Replace existing ${role} product?`,
    };
  }

  return { needed: false, message: '' };
};
