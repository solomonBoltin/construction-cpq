import { 
    QuotePreview, 
    CategoryPreview, 
    ProductPreview, 
    MaterializedProductEntry, 
    Quote,
    QuoteType,
    ProductRole,
    // CatalogStepKey, // Not used directly in this file
    MockFullQuote,
    // Product, // Not used directly in this file
    MockQuoteProductEntry,
    VariationGroupView,
    VariationOptionView,
    QuoteStatus,
    CalculatedQuote
} from '../types';
import { 
    // API_BASE_URL, // Not used directly in this file
    DEFAULT_QUOTE_CONFIG_ID, 
    FenceCategoryType, 
    GateCategoryType, 
    AddonCategoryType,
    // MOCKUP_DEFAULT_IMAGE // Not used directly in this file
} from '../constants';


// Simulating a persistent store for mock data
const mockDb = {
    quotes: [
        { id: 1, name: "Johnson Residence Fence", description: "Backyard privacy fence project.", status: QuoteStatus.CALCULATED, quote_type: QuoteType.FENCE_PROJECT, updated_at: "2025-06-10T14:48:00.000Z" },
        { id: 2, name: "Miller Commercial Property", description: "Perimeter security fence.", status: QuoteStatus.DRAFT, quote_type: QuoteType.FENCE_PROJECT, updated_at: "2025-06-09T11:20:00.000Z" },
        { id: 3, name: "Davis Garden Gate", description: "Small gate installation.", status: QuoteStatus.DRAFT, quote_type: QuoteType.FENCE_PROJECT, updated_at: "2025-06-08T09:00:00.000Z" },
        { id: 4, name: "Smith Pool Enclosure", description: "Safety fence around the pool.", status: QuoteStatus.FINALIZED, quote_type: QuoteType.FENCE_PROJECT, updated_at: "2025-05-20T17:15:00.000Z" },
        { id: 5, name: "Wilson Ranch Fencing", description: "Large scale agricultural fencing.", status: QuoteStatus.DRAFT, quote_type: QuoteType.FENCE_PROJECT, updated_at: "2025-06-11T10:05:00.000Z" },
    ] as QuotePreview[],
    categories: [
        { id:1, name: "Wood Fence", image_url: "https://placehold.co/400x300/a1887f/ffffff?text=Wood", type: FenceCategoryType },
        { id:2, name: "Vinyl Fence", image_url: "https://placehold.co/400x300/f5f5f5/333333?text=Vinyl", type: FenceCategoryType },
        { id:3, name: "Chain Link Fence", image_url: "https://placehold.co/400x300/9e9e9e/ffffff?text=Chain+Link", type: FenceCategoryType },
        { id:4, name: "Gates", image_url: "https://placehold.co/400x300/795548/ffffff?text=Gates", type: GateCategoryType },
        { id:5, name: "Project Add-ons", image_url: "https://placehold.co/400x300/455a64/ffffff?text=Add-ons", type: AddonCategoryType },
    ] as CategoryPreview[],
    products: [
        { id: 101, category_name: "Wood Fence", name: "6ft Dog Ear Privacy Fence", description: "Classic and affordable wood privacy fence.", image_url: "https://placehold.co/400x300/c8bbaE/ffffff?text=Dog+Ear" },
        { id: 102, category_name: "Wood Fence", name: "6ft Board on Board Fence", description: "Provides maximum privacy with overlapping boards.", image_url: "https://placehold.co/400x300/a1887f/ffffff?text=Board+on+Board" },
        { id: 201, category_name: "Vinyl Fence", name: "6ft White Vinyl Privacy", description: "Durable, low-maintenance privacy solution.", image_url: "https://placehold.co/400x300/e0e0e0/333333?text=White+Vinyl" },
        { id: 202, category_name: "Vinyl Fence", name: "4ft Picket Vinyl Fence", description: "Charming and traditional picket style.", image_url: "https://placehold.co/400x300/fafafa/333333?text=Picket+Vinyl" },
        { id: 301, category_name: "Chain Link Fence", name: "6ft Galvanized Chain Link", description: "Secure and durable for residential or commercial use.", image_url: "https://placehold.co/400x300/bdbdbd/ffffff?text=Galvanized" },
        { id: 401, category_name: "Gates", name: "4ft Wide Walk Gate", description: "Standard pedestrian gate, matches fence style.", image_url: "https://placehold.co/400x300/8d6e63/ffffff?text=Walk+Gate" },
        { id: 402, category_name: "Gates", name: "12ft Wide Drive Gate", description: "Double gate for vehicle access.", image_url: "https://placehold.co/400x300/6d4c41/ffffff?text=Drive+Gate" },
        { id: 501, category_name: "Project Add-ons", name: "Old Fence Teardown", description: "Removal and disposal of an existing fence (per foot).", image_url: "https://placehold.co/400x300/f44336/ffffff?text=Teardown" },
        { id: 502, category_name: "Project Add-ons", name: "Hard Digging", description: "Additional labor for rocky or difficult soil (per foot).", image_url: "https://placehold.co/400x300/757575/ffffff?text=Hard+Dig" },
    ] as ProductPreview[],
    product_details: { // Using VariationGroupView and VariationOptionView
        101: { variation_groups: [ { id: 1001, name: "Length (ft)", product_id: 101, selection_type: "single_choice", is_required: true, options: [] }, { id: 1002, name: "Wood Stain", product_id: 101, selection_type: "single_choice", is_required: false, options: [ { id: 1, name: "None", value_description: "Natural wood", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1002, is_selected: true }, { id: 2, name: "Cedar", value_description: "Rich red tones", additional_price: "2.50", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1002, is_selected: false }, { id: 3, name: "Redwood", value_description: "Deep brown tones", additional_price: "2.75", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1002, is_selected: false } ] } ] },
        102: { variation_groups: [ { id: 1001, name: "Length (ft)", product_id: 102, selection_type: "single_choice", is_required: true, options: [] }, { id: 1003, name: "Post Caps", product_id: 102, selection_type: "single_choice", is_required: false, options: [ { id: 4, name: "Flat Top", value_description: "Simple and modern", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1003, is_selected: true }, { id: 5, name: "Pyramid", value_description: "Decorative pointed cap", additional_price: "1.50", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1003, is_selected: false } ] } ] },
        201: { variation_groups: [ { id: 1001, name: "Length (ft)", product_id: 201, selection_type: "single_choice", is_required: true, options: [] }, { id: 1004, name: "Color", product_id: 201, selection_type: "single_choice", is_required: false, options: [ { id: 6, name: "White", value_description: "Classic white", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1004, is_selected: true }, { id: 7, name: "Tan", value_description: "Earthy tan color", additional_price: "1.00", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1004, is_selected: false }, { id: 8, name: "Gray", value_description: "Modern gray", additional_price: "1.25", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1004, is_selected: false } ] } ] },
        202: { variation_groups: [ { id: 1001, name: "Length (ft)", product_id: 202, selection_type: "single_choice", is_required: true, options: [] } ] },
        301: { variation_groups: [ { id: 1001, name: "Length (ft)", product_id: 301, selection_type: "single_choice", is_required: true, options: [] }, { id: 1005, name: "Privacy Slats", product_id: 301, selection_type: "single_choice", is_required: false, options: [ { id: 9, name: "None", value_description: "Standard visibility", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1005, is_selected: true }, { id: 10, name: "Green", value_description: "Adds privacy", additional_price: "3.00", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1005, is_selected: false }, { id: 11, name: "Black", value_description: "Adds privacy", additional_price: "3.00", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1005, is_selected: false } ] } ] },
        401: { variation_groups: [ { id: 1006, name: "Hardware", product_id: 401, selection_type: "single_choice", is_required: true, options: [ { id: 12, name: "Standard Latch", value_description: "Basic gravity latch", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1006, is_selected: true }, { id: 13, name: "Keyed Lock", value_description: "Secure locking latch", additional_price: "45.00", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1006, is_selected: false } ] } ] },
        402: { variation_groups: [ { id: 1007, name: "Automation", product_id: 402, selection_type: "single_choice", is_required: false, options: [ { id: 14, name: "Manual", value_description: "Opens by hand", additional_price: "0", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1007, is_selected: true }, { id: 15, name: "Automatic Opener", value_description: "Includes motor and remote", additional_price: "1200.00", price_multiplier:"1", additional_labor_cost_per_product_unit:"0", variation_group_id:1007, is_selected: false } ] } ] },
        501: { variation_groups: [ { id: 1008, name: "Length to Remove (ft)", product_id: 501, selection_type: "single_choice", is_required: true, options: [] } ] },
        502: { variation_groups: [ { id: 1009, name: "Length of Hard Dig (ft)", product_id: 502, selection_type: "single_choice", is_required: true, options: [] } ] },
    } as Record<number, { variation_groups: VariationGroupView[] }>,
    active_quotes: {} as Record<number, MockFullQuote>, // Stores full quote data being worked on
    calculated_quotes: {} as Record<number, CalculatedQuote>
};

// Ensure product details have product_id in variation groups and options
Object.values(mockDb.product_details).forEach(detail => {
    detail.variation_groups.forEach(group => {
        group.options.forEach(opt => {
            if (!opt.variation_group_id) opt.variation_group_id = group.id;
        });
    });
});


const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const quoteProcessMockApi = {
    listQuotes: async (quoteType?: QuoteType, offset: number = 0, limit: number = 100): Promise<QuotePreview[]> => {
        await delay(300);
        let results = mockDb.quotes;
        if (quoteType) {
            results = results.filter(q => q.quote_type === quoteType);
        }
        return results.slice(offset, offset + limit);
    },

    createQuote: async (name: string, quote_type: QuoteType, description?: string, config_id: number = DEFAULT_QUOTE_CONFIG_ID): Promise<Quote> => {
        await delay(300);
        const newId = Math.max(0, ...mockDb.quotes.map(q => q.id)) + 1;
        const now = new Date().toISOString();
        const newQuotePreview: QuotePreview = {
            id: newId,
            name: name,
            description: description || "New project",
            status: QuoteStatus.DRAFT,
            quote_type: quote_type,
            updated_at: now,
        };
        mockDb.quotes.push(newQuotePreview);

        const newFullQuote: MockFullQuote = {
            ...newQuotePreview,
            product_entries: []
        };
        mockDb.active_quotes[newId] = newFullQuote;
        
        // Return a Quote-like object (as if from backend)
        // Casting to unknown first if types are not perfectly assignable but structurally compatible for the purpose of the mock.
        return {
            ...newFullQuote,
            quote_config_id: config_id,
            created_at: now,
            ui_state: null,
        } as unknown as Quote; // Adjusted cast due to deeper differences in product_entries element types (role, selected_variations)
    },
    
    // This is a helper for the frontend to get the "active working copy"
    getQuoteForEditing: async (id: number): Promise<MockFullQuote | null> => {
        await delay(100);
        if (!mockDb.active_quotes[id]) {
            const quoteBase = mockDb.quotes.find(q => q.id === id);
            if (quoteBase) {
                 // Simulate fetching entries if it were a real backend.
                 // For mock, we'll initialize with empty if not found.
                mockDb.active_quotes[id] = { ...quoteBase, product_entries: [] };
            } else {
                return null;
            }
        }
        return JSON.parse(JSON.stringify(mockDb.active_quotes[id])); // Return a copy
    },

    listCategories: async (categoryType?: string, offset: number = 0, limit: number = 100): Promise<CategoryPreview[]> => {
        await delay(200);
        let results = mockDb.categories;
        if (categoryType) {
            results = results.filter(c => c.type === categoryType);
        }
        return results.slice(offset, offset + limit);
    },

    listProductsInCategory: async (categoryName: string, offset: number = 0, limit: number = 100): Promise<ProductPreview[]> => {
        await delay(200);
        const results = mockDb.products.filter(p => p.category_name === categoryName);
        return results.slice(offset, offset + limit);
    },
    
    listProductsByCategoryType: async (categoryType: string, offset: number = 0, limit: number = 100): Promise<ProductPreview[]> => {
        await delay(200);
        // Find all categories of this type
        const categoryNames = mockDb.categories.filter(c => c.type === categoryType).map(c => c.name);
        const results = mockDb.products.filter(p => p.category_name && categoryNames.includes(p.category_name));
        return results.slice(offset, offset + limit);
    },
    
    // This combines fetching product entry and materializing it for the mock
    getMaterializedProductEntry: async (productEntryId: number): Promise<MaterializedProductEntry | null> => {
        await delay(150);

        // Find the entry in all active quotes
        const entry = Object.values(mockDb.active_quotes).flatMap(q => q.product_entries).find(e => e.id === productEntryId);
        if (!entry) return null; // Not found
        
        const product = mockDb.products.find(p => p.id === entry.product_id);
        if (!product) return null;

        let details = JSON.parse(JSON.stringify(mockDb.product_details[entry.product_id] || { variation_groups: [] }));

        // Sync selections from entry.selected_variations
        details.variation_groups.forEach((group: VariationGroupView) => {
            group.options.forEach((opt: VariationOptionView) => {
                const isSelected = entry.selected_variations.some(sv => sv.group_id === group.id && sv.option_id === opt.id);
                opt.is_selected = isSelected;

                // Ensure options have variation_group_id (added during mockDb init)
                 if (!opt.variation_group_id) opt.variation_group_id = group.id;
            });
        });
        
        return {
            id: entry.id,
            quote_id: entry.quote_id,
            product_id: entry.product_id,
            product_name: product.name,
            role: entry.role as ProductRole,
            quantity_of_product_units: entry.quantity_of_product_units, // Use renamed field
            notes: entry.notes,
            variation_groups: details.variation_groups
        };
    },

    addQuoteProductEntry: async (quoteId: number, productId: number, quantity: number, role: ProductRole): Promise<MockQuoteProductEntry> => {
        await delay(250);
        const quote = mockDb.active_quotes[quoteId];
        if (!quote) throw new Error("Quote not found");

        const product = mockDb.products.find(p => p.id === productId);
        if (!product) throw new Error("Product not found");

        if (role === ProductRole.MAIN || role === ProductRole.SECONDARY) {
            const existingIndex = quote.product_entries.findIndex(e => e.role === role);
            if (existingIndex > -1) {
                quote.product_entries.splice(existingIndex, 1);
            }
        }
        
        const newEntry: MockQuoteProductEntry = {
            id: Date.now(),
            quote_id: quoteId,
            product_id: productId,
            role: role,
            quantity_of_product_units: quantity, // Use renamed field
            notes: "",
            selected_variations: [], 
        };
        quote.product_entries.push(newEntry);
        mockDb.active_quotes[quoteId] = {...quote}; // Ensure update
        return newEntry;
    },

    deleteQuoteProductEntry: async (quoteId: number, productEntryId: number): Promise<void> => {
        await delay(200);
        const quote = mockDb.active_quotes[quoteId];
        if (!quote) throw new Error("Quote not found");
        quote.product_entries = quote.product_entries.filter(e => e.id !== productEntryId);
        mockDb.active_quotes[quoteId] = {...quote};
    },
    
    updateQuoteProductEntry: async (quoteId: number, productEntryId: number, data: { quantity?: number; notes?: string }): Promise<MockQuoteProductEntry> => {
        await delay(150);
        const quote = mockDb.active_quotes[quoteId];
        if (!quote) throw new Error("Quote not found");
        const entry = quote.product_entries.find(e => e.id === productEntryId);
        if (!entry) throw new Error("Entry not found");

        if (data.quantity !== undefined) entry.quantity_of_product_units = data.quantity; // Use renamed field
        if (data.notes !== undefined) entry.notes = data.notes;
        mockDb.active_quotes[quoteId] = {...quote};
        return entry;
    },

    setQuoteProductVariationOption: async (quoteId: number, productEntryId: number, variationGroupId: number, variationOptionId: number): Promise<MockQuoteProductEntry> => {
        await delay(150);
        const quote = mockDb.active_quotes[quoteId];
        if (!quote) throw new Error("Quote not found");
        const entry = quote.product_entries.find(e => e.id === productEntryId);
        if (!entry) throw new Error("Entry not found");

        const productDetails = mockDb.product_details[entry.product_id];
        if (!productDetails) throw new Error("Product details not found");

        const groupDefinition = productDetails.variation_groups.find(g => g.id === variationGroupId);
        if(!groupDefinition) throw new Error("Variation group definition not found");


        // let existingSelectionForGroup = entry.selected_variations.find(sv => sv.group_id === variationGroupId); // Not directly used below

        if (groupDefinition.selection_type === 'single_choice') {
            // Remove any existing selection for this group, then add the new one.
            entry.selected_variations = entry.selected_variations.filter(sv => sv.group_id !== variationGroupId);
            entry.selected_variations.push({ group_id: variationGroupId, option_id: variationOptionId });
        } else if (groupDefinition.selection_type === 'multi_choice') {
            // For multi-choice, toggle. This wasn't in mockup HTML but is typical.
            // Mockup HTML logic implies single choice for all variations. We follow that.
            // If mockup logic was: if option selected, it IS the selected one for the group.
             entry.selected_variations = entry.selected_variations.filter(sv => sv.group_id !== variationGroupId);
             entry.selected_variations.push({ group_id: variationGroupId, option_id: variationOptionId });
        }
        
        mockDb.active_quotes[quoteId] = {...quote};
        return entry;
    },

    calculateQuote: async (quoteId: number): Promise<CalculatedQuote> => {
        await delay(1000);
        const quote = mockDb.active_quotes[quoteId];
        if (!quote) throw new Error("Quote not found to calculate.");

        let totalMaterialCost = 0;
        let totalLaborCost = 0;

        quote.product_entries.forEach(entry => {
            // Gross simplification for mock
            totalMaterialCost += entry.quantity_of_product_units * (Math.random() * 50 + 20); // Random material cost per unit
            totalLaborCost += entry.quantity_of_product_units * (Math.random() * 20 + 10); // Random labor cost per unit
        });
        
        const costOfGoodsSold = totalMaterialCost + totalLaborCost;
        // Apply some mock rates
        const marginAmount = costOfGoodsSold * 0.3; // 30% margin
        const subtotalBeforeTax = costOfGoodsSold + marginAmount;
        const taxAmount = subtotalBeforeTax * 0.08; // 8% tax
        const finalPrice = subtotalBeforeTax + taxAmount;

        const calculated: CalculatedQuote = {
            id: Date.now(),
            quote_id: quoteId,
            total_material_cost: totalMaterialCost.toFixed(2),
            total_labor_cost: totalLaborCost.toFixed(2),
            cost_of_goods_sold: costOfGoodsSold.toFixed(2),
            applied_rates_info_json: [
                { name: "Margin", type: "margin", rate_value: "0.30", applied_amount: marginAmount.toFixed(2) }
            ],
            subtotal_before_tax: subtotalBeforeTax.toFixed(2),
            tax_amount: taxAmount.toFixed(2),
            final_price: finalPrice.toFixed(2),
            calculated_at: new Date().toISOString(),
            bill_of_materials_json: quote.product_entries.map(entry => ({
                material_name: `Materials for Product ${entry.product_id}`,
                quantity: entry.quantity_of_product_units.toString(), // Use renamed field
                unit_cost: (totalMaterialCost / (quote.product_entries.length * entry.quantity_of_product_units || 1)).toFixed(2), // Use renamed field
                total_cost: (totalMaterialCost / quote.product_entries.length).toFixed(2), // Simplification
                unit_name: "unit"
            }))
        };
        mockDb.calculated_quotes[quoteId] = calculated;
        
        // Update quote status in the main list
        const quoteInList = mockDb.quotes.find(q => q.id === quoteId);
        if (quoteInList) {
            quoteInList.status = QuoteStatus.CALCULATED;
            quoteInList.updated_at = new Date().toISOString();
        }

        return calculated;
    },

    getCalculatedQuote: async (quoteId: number): Promise<CalculatedQuote | null> => {
        await delay(200);
        return mockDb.calculated_quotes[quoteId] || null;
    }
};