// Enums from models.py
export enum QuoteType {
    GENERAL = "general",
    FENCE_PROJECT = "fence_project",
    DECK_PROJECT = "deck_project",
}

export enum QuoteStatus {
    DRAFT = "DRAFT",
    FINAL = "FINAL",
    SENT = "SENT",
    // Adding frontend/mockup statuses
    CALCULATED = "calculated", // from mockup
    FINALIZED = "finalized" // from mockup
}

export enum ProductRole {
    DEFAULT = "DEFAULT",
    MAIN = "MAIN",
    SECONDARY = "SECONDARY",
    ADDITIONAL = "ADDITIONAL",
}

// Pydantic models for JSONB fields
export interface BillOfMaterialEntry {
    material_name: string;
    quantity: string; // Decimal as string
    unit_cost: string; // Decimal as string
    total_cost: string; // Decimal as string
    unit_name?: string | null;
    cull_units?: string | null; // Decimal as string
    leftovers?: string | null; // Decimal as string
}

export interface AppliedRateInfoEntry {
    name: string;
    type: string;
    rate_value: string; // Decimal as string
    applied_amount: string; // Decimal as string
}

// SQLModel Table Models (Frontend representations)
export interface UnitType {
    id: number;
    name: string;
    category: string;
}

export interface ProductCategory {
    id: number;
    name: string;
    type: string;
    image_url?: string | null;
}

export interface Material {
    id: number;
    name: string;
    description?: string | null;
    cost_per_supplier_unit: string; // Decimal
    supplier_unit_type_id?: number | null;
    quantity_in_supplier_unit: string; // Decimal
    base_unit_type_id: number;
    cull_rate?: number | null; // float
}

export interface Product {
    id: number;
    name: string;
    description?: string | null;
    product_unit_type_id: number;
    unit_labor_cost: string; // Decimal
    image_url?: string | null;
    // For mock data consistency from frontend_mockup.html
    category_name?: string; 
}

export interface VariationOption {
    id: number;
    name: string;
    variation_group_id: number;
    value_description?: string | null;
    additional_price: string; // Decimal
    price_multiplier: string; // Decimal
    additional_labor_cost_per_product_unit: string; // Decimal
}

export interface VariationGroup {
    id: number;
    name: string;
    product_id: number;
    selection_type: string; // 'single_choice', 'multi_choice'
    is_required: boolean;
    options: VariationOption[];
}

export interface QuoteConfig {
    id: number;
    name: string;
    margin_rate: string; // Decimal
    tax_rate: string; // Decimal
    // ... other fields
}

export interface Quote {
    id: number;
    name?: string | null;
    description?: string | null;
    quote_config_id: number;
    status: QuoteStatus | string; // Allow string for mockup values
    quote_type: QuoteType;
    ui_state?: string | null;
    created_at: string; // datetime
    updated_at: string; // datetime
    product_entries: QuoteProductEntry[]; // Added for active quote state
}

export interface QuoteProductEntry {
    id: number; // Can be Date.now() for mock frontend temporary ID
    quote_id: number;
    product_id: number;
    quantity_of_product_units: number; // Decimal in backend, number for frontend ease
    notes?: string | null;
    role: ProductRole;
    selected_variations: QuoteProductEntryVariation[]; // Simplified for mock
}

// Mock specific selected_variations from HTML
export interface MockSelectedVariation {
    group_id: number;
    option_id: number;
}


export interface QuoteProductEntryVariation {
    id: number;
    quote_product_entry_id: number;
    variation_option_id: number;
    // For frontend use, to map back to group
    variation_group_id?: number; 
}


export interface CalculatedQuote {
    id: number;
    quote_id: number;
    bill_of_materials_json?: BillOfMaterialEntry[] | null;
    total_material_cost: string; // Decimal
    total_labor_cost: string; // Decimal
    cost_of_goods_sold: string; // Decimal
    applied_rates_info_json?: AppliedRateInfoEntry[] | null;
    subtotal_before_tax: string; // Decimal
    tax_amount: string; // Decimal
    final_price: string; // Decimal
    calculated_at: string; // datetime
}


// Frontend specific DTOs from quote_process_service.py and mockup
export interface QuotePreview {
    id: number;
    name?: string | null;
    description?: string |null;
    status: QuoteStatus | string; // Allow string for mockup values
    quote_type: QuoteType;
    updated_at: string; // datetime
}

export interface CategoryPreview {
    name: string;
    image_url?: string | null;
    // Added from mockup, consistent with ProductCategory
    id?: number; 
    type?: string;
}

export interface ProductPreview {
    id: number;
    name: string;
    description?: string | null;
    image_url?: string | null;
    category_name?: string; // From mockup db.products
}

export interface VariationOptionView extends VariationOption {
    is_selected: boolean;
    // additional_price is string in VariationOption, but number in mockup. Standardize to string from API, parse to number for UI.
    // For consistency with mockup, we'll allow number here if needed, but prefer string and parse.
    // The base VariationOption already has additional_price: string.
}

export interface VariationGroupView extends VariationGroup {
    options: VariationOptionView[];
}

export interface MaterializedProductEntry {
    id: number; // This is QuoteProductEntry.id
    quote_id: number;
    product_id: number;
    product_name: string;
    role?: ProductRole | null;
    quantity_of_product_units: number; // Using number for UI, was Decimal in backend
    notes?: string | null;
    variation_groups: VariationGroupView[];
}

// For mock data to represent QuoteProductEntry from frontend_mockup.html more closely
export interface MockQuoteProductEntry extends QuoteProductEntry {
    // Mock data often has richer details for UI simulation
    product_name: string;
    product_image_url?: string;
    product_unit_name: string;
    // selected_variations is simplified in mock from the backend's relational model
    selected_variations: MockSelectedVariation[];
    notes?: string; // Allow notes to be optional to align with base type
}

export interface MockFullQuote extends QuotePreview {
    product_entries: MockQuoteProductEntry[];
}


// Application specific states
export type AppView = 'quote_list' | 'catalog';

export type CatalogStepKey = 
  | 'choose_category' 
  | 'choose_main_product' 
  | 'configure_main' 
  | 'choose_secondary_product' 
  | 'configure_secondary' 
  | 'select_additional' 
  | 'review';

export interface CatalogContextState {
    selectedCategoryName: string | null; // For main product
    activeProductEntryId: number | null; // QuoteProductEntry.id being configured
    // This will hold the "materialized" version of the active quote
    activeQuoteFull?: MockFullQuote | null; 
}