import { ComponentType } from 'react';
import { QuoteBuilderStepKey, FullQuote, ProductRole } from '../types';

// Import step components
import CategorySelectorStep from '../components/quote_builder/steps/CategorySelectorStep';
import ProductSelectorStep from '../components/quote_builder/steps/ProductSelectorStep';
import ProductConfiguratorStep from '../components/quote_builder/steps/ProductConfiguratorStep';
import AdditionalProductSelectorStep from '../components/quote_builder/steps/AdditionalProductSelectorStep';
import ReviewStep from '../components/quote_builder/steps/ReviewStep';

// Product role configuration for managing limits and confirmations
export const PRODUCT_ROLE_CONFIG = {
  [ProductRole.MAIN]: {
    maxCount: 1,
    requiresConfirmationToReplace: true,
    confirmationMessage: 'You already have a main fence product selected. Would you like to replace it with this one?',
  },
  [ProductRole.SECONDARY]: {
    maxCount: 1,
    requiresConfirmationToReplace: true,
    confirmationMessage: 'You already have a gate product selected. Would you like to replace it with this one?',
  },
  [ProductRole.ADDITIONAL]: {
    maxCount: null, // No limit
    requiresConfirmationToReplace: false,
  },
  [ProductRole.DEFAULT]: {
    maxCount: null, // No limit
    requiresConfirmationToReplace: false,
  },
} as const;

interface StepConfig {
  key: QuoteBuilderStepKey;
  label: string;
  component: ComponentType<any>;
  props?: any;
  canProceed?: (quote: FullQuote | null, selectedCategoryName: string | null) => boolean;
  isCompleted?: (quote: FullQuote | null, selectedCategoryName: string | null) => boolean;
}

export const STEPS: StepConfig[] = [
  {
    key: 'choose_category',
    label: 'Choose Category',
    component: CategorySelectorStep,
    canProceed: (quote, selectedCategoryName) => {
      // Can proceed if category selected OR main product exists
      return !!selectedCategoryName || !!quote?.product_entries.find(e => e.role === ProductRole.MAIN);
    },
    isCompleted: (quote, selectedCategoryName) => {
      // Completed if category selected OR main product exists
      return !!selectedCategoryName || !!quote?.product_entries.find(e => e.role === ProductRole.MAIN);
    },
  },
  {
    key: 'choose_main_product',
    label: 'Select Main Product',
    component: ProductSelectorStep,
    props: { role: ProductRole.MAIN },
    canProceed: (quote, selectedCategoryName) => {
      // Can proceed if main product is selected OR if category is selected
      const hasMainProduct = !!quote?.product_entries.find(e => e.role === ProductRole.MAIN);
      return hasMainProduct || !!selectedCategoryName;
    },
    isCompleted: (quote) => {
      // Completed when main product exists
      return !!quote?.product_entries.find(e => e.role === ProductRole.MAIN);
    },
  },
  {
    key: 'configure_main',
    label: 'Configure Main Product',
    component: ProductConfiguratorStep,
    props: { role: ProductRole.MAIN },
    canProceed: (quote) => {
      const mainEntry = quote?.product_entries.find(e => e.role === ProductRole.MAIN);
      // Can proceed if main product is configured with quantity
      return !!mainEntry && mainEntry.quantity_of_product_units > 0;
    },
    isCompleted: (quote) => {
      const mainEntry = quote?.product_entries.find(e => e.role === ProductRole.MAIN);
      // Completed when main product has quantity > 0
      return !!mainEntry && mainEntry.quantity_of_product_units > 0;
    },
  },
  {
    key: 'choose_secondary_product',
    label: 'Select Gate',
    component: ProductSelectorStep,
    props: { role: ProductRole.SECONDARY },
    canProceed: (quote) => {
      const mainEntry = quote?.product_entries.find(e => e.role === ProductRole.MAIN);
      const hasSecondaryProduct = !!quote?.product_entries.find(e => e.role === ProductRole.SECONDARY);
      // Can proceed if main product is configured OR if secondary already exists
      return (!!mainEntry && mainEntry.quantity_of_product_units > 0) || hasSecondaryProduct;
    },
    isCompleted: (quote) => {
      // Completed when secondary product exists
      return !!quote?.product_entries.find(e => e.role === ProductRole.SECONDARY);
    },
  },
  {
    key: 'configure_secondary',
    label: 'Configure Gate',
    component: ProductConfiguratorStep,
    props: { role: ProductRole.SECONDARY },
    canProceed: (quote) => {
      const secondaryEntry = quote?.product_entries.find(e => e.role === ProductRole.SECONDARY);
      // Can proceed if secondary product is configured with quantity
      return !!secondaryEntry && secondaryEntry.quantity_of_product_units > 0;
    },
    isCompleted: (quote) => {
      const secondaryEntry = quote?.product_entries.find(e => e.role === ProductRole.SECONDARY);
      // Completed when secondary product has quantity > 0
      return !!secondaryEntry && secondaryEntry.quantity_of_product_units > 0;
    },
  },
  {
    key: 'select_additional',
    label: 'Additional Services',
    component: AdditionalProductSelectorStep,
    canProceed: () => true, // Optional step - always can proceed
    isCompleted: () => false, // Never shows as completed, just enabled
  },
  {
    key: 'review',
    label: 'Review & Calculate',
    component: ReviewStep,
    canProceed: () => true, // Final step - always can proceed
    isCompleted: () => false, // Never shows as completed
  },
];

export const QUOTE_BUILDER_CONFIG = {
  // UI Configuration
  ui: {
    loadingTimeout: 30000, // 30 seconds
    debounceDelay: 500, // 500ms for input debouncing
    autoSaveDelay: 2000, // 2 seconds for auto-save
    maxFileSize: 5 * 1024 * 1024, // 5MB max file upload
  },

  // Validation rules
  validation: {
    product: {
      minQuantity: 1,
      maxQuantity: 1000,
      maxDescriptionLength: 500
    },
    quote: {
      maxNameLength: 100,
      maxDescriptionLength: 1000
    }
  },

  // Feature flags
  features: {
    autoSave: true,
    realTimeCalculation: false,
    advancedConfiguration: true,
    bulkOperations: false
  },

  // Error messages
  messages: {
    errors: {
      loadQuote: 'Failed to load quote',
      updateEntry: 'Failed to update product',
      selectProduct: 'Failed to select product',
      calculate: 'Failed to calculate quote',
    },
    loading: {
      loadingQuote: 'Loading quote...',
      calculating: 'Calculating quote...',
      updating: 'Updating...',
    },
  },
} as const;

// Type-safe configuration access
export type QuoteBuilderConfig = typeof QUOTE_BUILDER_CONFIG;
