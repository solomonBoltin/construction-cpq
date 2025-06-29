import { CatalogStepKey } from './types';

export const API_DOMAIN = "http://localhost:8000"; // From user plan
export const API_BASE_URL = API_DOMAIN + "/api/v1"; // From user plan

export const DEFAULT_QUOTE_CONFIG_ID = 1;

export const FenceCategoryType = "fence"; // for getting categories by type 
export const GateCategoryType = "gate";
export const AddonCategoryType = "additional"; // from mockup categories

export const Steps: Array<{ key: CatalogStepKey, label: string }> = [
    { key: 'choose_category', label: 'Category' },
    { key: 'choose_main_product', label: 'Main Product' },
    { key: 'configure_main', label: 'Configure Main' },
    { key: 'choose_secondary_product', label: 'Secondary Product' }, // Typically gates
    { key: 'configure_secondary', label: 'Configure Secondary' },
    { key: 'select_additional', label: 'Add-ons' },
    { key: 'review', label: 'Review' },
];

export const MOCKUP_DEFAULT_IMAGE = "https://placehold.co/400x300/e2e8f0/64748b?text=Image";