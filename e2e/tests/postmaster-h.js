// /tests/product_scenarios/postmaster_h_100ft_test.js

const cpqClient = require('../cpq_backend_client');
const assert = require('assert');
const { Decimal } = require('decimal.js');

/**
 * ==================================================================================
 * CONFIGURATION
 * ==================================================================================
 * This object holds all the input parameters that match the Excel calculator.
 * You can change these values to test different fence configurations.
 */
const config = {
    // Job Parameters from Excel 'Postmaster-Horizontal' sheet
    jobSize: new Decimal(100.0),      // B3: Job Size (feet)
    woodType: 'JPC',                  // B5: Wood Type ('WRC' or 'JPC')
    orderType: 'Job Lot',             // B6: Order Type ('Bulk' or 'Job Lot')
    finish: 'Stained',                // B7: Finish ('Raw' or 'Stained')
    style: 'BoB',                     // B8: Type ('SxS' or 'BoB')
    cap: 'no',                        // B9: Cap? ('yes' or 'no')
    trim: 'No',                       // B10: Trim? ('Yes' or 'No')
    height: new Decimal(8.0),         // B11: Height (6 or 8)

    // Financial Rates from Excel
    salesTaxRate: new Decimal(0.085), // B13: Sales Tax Rate
    picketCullRate: new Decimal(0.05),// B14: Picket Cull Rate
    salesCommissionRate: new Decimal(0.07), // C32: Sales Commission
    franchiseFeeRate: new Decimal(0.04), // C33: Franchise Fee
    marginRate: new Decimal(0.30),     // C35: Margin
};

// ==================================================================================
// EXPECTED RESULTS FROM EXCEL (for the configuration above)
// ==================================================================================
// These values are taken directly from the Excel sheet for the config above.
// The test will assert that the API's calculations match these numbers.
const expectedResults = {
    jobTotal: new Decimal('6537.16'), // F43: Total Job Price (rounded from 6537.161...)
    materialSubtotal: new Decimal('3108.71'), // F29: Material Subtotal (rounded from 3108.711...)
    installPerFt: new Decimal('13'), // D30: Install/ft for 8' BoB
    cogs: new Decimal('4408.71'), // F31: COGS
    finalPrice: new Decimal('6537.16') // F43: Final calculated price, rounded to 2 decimal places.
};


/**
 * Main test function for the Postmaster-Horizontal 100ft scenario.
 */
async function postmasterHorizontal100ftTest() {
    console.log('▶️  Starting Test: Postmaster-Horizontal 100ft Scenario');

    // Store IDs of all created database records for cleanup
    const createdIds = {
        unitTypes: [],
        materials: [],
        products: [],
        variationGroups: [],
        variationOptions: [],
        quoteConfigs: [],
        quotes: [],
    };

    try {
        // --- 1. SETUP: Create prerequisite data (Unit Types, Materials) ---
        console.log('   1. Setting up prerequisite data...');
        const { unitTypes, materials } = await createPrerequisites(createdIds);
        console.log('   ✅ Prerequisite data created successfully.');

        // --- 2. PRODUCT CREATION: Define the configurable fence product ---
        console.log('   2. Creating the "Postmaster Horizontal" product with all variations...');
        const { productId, variationOptions } = await createConfigurableProduct(createdIds, unitTypes, materials);
        createdIds.products.push(productId);
        console.log(`   ✅ Product created successfully with ID: ${productId}`);

        // --- 3. QUOTE CONFIGURATION: Set up financial parameters ---
        console.log('   3. Creating QuoteConfig with financial rates...');
        const quoteConfigId = await createQuoteConfig(createdIds);
        console.log(`   ✅ QuoteConfig created successfully with ID: ${quoteConfigId}`);

        // --- 4. QUOTE GENERATION & CALCULATION ---
        console.log('   4. Creating and calculating the quote...');
        const quoteId = await createAndConfigureQuote(createdIds, productId, quoteConfigId, variationOptions);
        console.log(`   ✅ Quote created successfully with ID: ${quoteId}`);
        
        console.log(`   ...Calculating quote ${quoteId}...`);
        const calculatedQuote = await cpqClient.quote.calculate(quoteId);
        assert(calculatedQuote, 'Quote calculation failed to return a result.');
        console.log('   ✅ Quote calculated successfully.');


        // --- 5. ASSERTIONS: Verify the calculated results ---
        console.log('   5. Verifying calculated quote against Excel results...');
        assert.ok(calculatedQuote.final_price, 'Final price is missing from calculation result.');

        const finalPrice = new Decimal(calculatedQuote.final_price);
        
        // We round to 2 decimal places to match currency representation
        const roundedFinalPrice = finalPrice.toDecimalPlaces(2, Decimal.ROUND_HALF_UP);
        const roundedExpectedPrice = expectedResults.finalPrice.toDecimalPlaces(2, Decimal.ROUND_HALF_UP);

        assert.strictEqual(
            roundedFinalPrice.toString(),
            roundedExpectedPrice.toString(),
            `Final price mismatch! API: ${roundedFinalPrice.toString()}, Expected (Excel): ${roundedExpectedPrice.toString()}`
        );
        console.log(`   ✅ SUCCESS: Final price matches Excel! [API: ${roundedFinalPrice}, Excel: ${roundedExpectedPrice}]`);

        // Optional: Add more assertions for intermediate values if needed
        const cogs = new Decimal(calculatedQuote.cost_of_goods_sold).toDecimalPlaces(2, Decimal.ROUND_HALF_UP);
        assert.strictEqual(
            cogs.toString(),
            expectedResults.cogs.toDecimalPlaces(2, Decimal.ROUND_HALF_UP).toString(),
            `COGS mismatch! API: ${cogs}, Expected: ${expectedResults.cogs.toDecimalPlaces(2, Decimal.ROUND_HALF_UP)}`
        );
         console.log(`   ✅ COGS matches Excel.`);


    } catch (error) {
        console.error('   ❌ TEST FAILED:', error.message);
        if (error.response && error.response.body) {
            console.error('   API Error Response:', JSON.stringify(error.response.body, null, 2));
        } else if (error.stack) {
            console.error('   Stack Trace:', error.stack);
        }
        throw error; // Re-throw to fail the overall test run
    } finally {
        // --- 6. CLEANUP ---
        console.log('   6. Cleaning up created test data...');
        await cleanup(createdIds);
        console.log('   ✅ Cleanup complete.');
        console.log('⏹️  Finished Test: Postmaster-Horizontal 100ft Scenario');
    }
}


/**
 * Creates all necessary prerequisite data like UnitTypes and Materials.
 * @param {object} createdIds - Object to store the IDs of created entities.
 * @returns {object} - An object containing created unitTypes and materials maps.
 */
async function createPrerequisites(createdIds) {
    // Unit Types
    const unitTypeNames = ['each', 'feet', 'linear foot', 'bag', 'box'];
    const unitTypes = {};
    for (const name of unitTypeNames) {
        const newUnitType = await cpqClient.unitType.create({ name, category: "Test" });
        createdIds.unitTypes.push(newUnitType.id);
        unitTypes[name] = newUnitType.id;
    }

    // Materials from 'Mat_Costs' Sheet
    const materialData = [
        // Posts
        { name: "8' Postmaster", cost: '18.01', unit: 'each' },
        { name: "11' Postmaster", cost: '27.06', unit: 'each' },
        // Wood - JPC Raw
        { name: "JPC-Raw-1x6x8-Job Lot", cost: '5.40', unit: 'each' },
        { name: "JPC-Raw-2x4x8-Job Lot", cost: '9.00', unit: 'each' },
        { name: "JPC-Raw-2x4x12-Job Lot", cost: '12.50', unit: 'each' },
        // Wood - JPC Stained
        { name: "JPC-Stained-1x6x8-Job Lot", cost: '6.75', unit: 'each' },
        { name: "JPC-Stained-2x4x8-Job Lot", cost: '11.25', unit: 'each' },
        { name: "JPC-Stained-2x4x12-Job Lot", cost: '14.50', unit: 'each' },
        { name: "JPC-Stained-2x6x12-Job Lot", cost: '15.38', unit: 'each' }, // F16 in Mat_Costs seems to be a manual entry
        // Kickboard
        { name: "SYP-Color Treated-2x6x12-Bulk", cost: '9.18', unit: 'each' },
        // Hardware
        { name: 'Hardware - 2.25" Galvanized Ring Shank Nails', cost: '0.01', unit: 'each' },
        { name: 'Concrete', cost: '5.35', unit: 'bag' },
    ];
    
    const materials = {};
    for (const mat of materialData) {
        const newMaterial = await cpqClient.material.create({
            name: mat.name,
            cost_per_supplier_unit: mat.cost,
            supplier_unit_type_id: unitTypes[mat.unit],
            base_unit_type_id: unitTypes[mat.unit], // Assuming supplier and base units are the same for simplicity
        });
        createdIds.materials.push(newMaterial.id);
        materials[mat.name] = newMaterial.id;
    }

    return { unitTypes, materials };
}

/**
 * Creates the main configurable product and all its variation groups/options.
 * @param {object} createdIds - Object to store IDs.
 * @param {object} unitTypes - Map of unit type names to IDs.
 * @param {object} materials - Map of material names to IDs.
 * @returns {object} - An object with the productId and a map of variation options.
 */
async function createConfigurableProduct(createdIds, unitTypes, materials) {
    const product = await cpqClient.product.create({
        name: `Postmaster Horizontal Test Product ${Date.now()}`,
        description: 'A test product to replicate the Postmaster Horizontal calculator.',
        product_unit_type_id: unitTypes['linear foot'],
        base_labor_cost_per_product_unit: '13.00' // Base install cost for 8' BoB from Sub_Labor E11
    });

    const productId = product.id;
    
    // Base Materials (always included)
    const sectionWidth = config.height.equals(6) ? 8 : 6;
    const sectionsPer100Ft = config.jobSize.dividedBy(sectionWidth);

    await cpqClient.productMaterial.create({
        product_id: productId,
        material_id: materials["8' Postmaster"],
        quantity_of_material_base_units_per_product_unit: new Decimal(1).dividedBy(sectionWidth).toString()
    });
    await cpqClient.productMaterial.create({
        product_id: productId,
        material_id: materials['Concrete'],
        quantity_of_material_base_units_per_product_unit: new Decimal(1.5).dividedBy(sectionWidth).toString()
    });
     await cpqClient.productMaterial.create({
        product_id: productId,
        material_id: materials['Hardware - 2.25" Galvanized Ring Shank Nails'],
        quantity_of_material_base_units_per_product_unit: new Decimal(400).dividedBy(sectionWidth).toString()
    });
    await cpqClient.productMaterial.create({
        product_id: productId,
        material_id: materials['SYP-Color Treated-2x6x12-Bulk'],
        quantity_of_material_base_units_per_product_unit: new Decimal(0.5).dividedBy(sectionWidth).toString()
    });


    // Variation Groups & Options
    const variationOptions = {};

    // --- Height Group ---
    const heightGroup = await cpqClient.variationGroup.create({ name: 'Height', product_id: productId, is_required: true });
    createdIds.variationGroups.push(heightGroup.id);
    const opt8ft = await cpqClient.variationOption.create({ name: "8ft", variation_group_id: heightGroup.id });
    variationOptions['8ft'] = opt8ft.id;
    createdIds.variationOptions.push(opt8ft.id);


    // --- Style Group ---
    const styleGroup = await cpqClient.variationGroup.create({ name: 'Style', product_id: productId, is_required: true });
    createdIds.variationGroups.push(styleGroup.id);
    const optSxS = await cpqClient.variationOption.create({ name: "SxS", variation_group_id: styleGroup.id });
    const optBoB = await cpqClient.variationOption.create({ name: "BoB", variation_group_id: styleGroup.id });
    variationOptions['SxS'] = optSxS.id;
    variationOptions['BoB'] = optBoB.id;
    createdIds.variationOptions.push(optSxS.id, optBoB.id);

    // Add material difference for BoB vs SxS (22 pickets for BoB vs 16 for SxS on 8ft fence)
    const picketMaterialName = `JPC-Stained-1x6x8-Job Lot`;
    const basePickets = 16;
    const bobExtraPickets = 22 - 16;

    await cpqClient.productMaterial.create({ // Base pickets for SxS
        product_id: productId,
        material_id: materials[picketMaterialName],
        quantity_of_material_base_units_per_product_unit: new Decimal(basePickets).times(1 + config.picketCullRate).dividedBy(sectionWidth).toString()
    });
     await cpqClient.variationOptionMaterial.create({ // Extra pickets for BoB
        variation_option_id: optBoB.id,
        material_id: materials[picketMaterialName],
        quantity_of_material_base_units_added: new Decimal(bobExtraPickets).times(1 + config.picketCullRate).dividedBy(sectionWidth).toString(),
    });

    // --- Finish Group ---
    const finishGroup = await cpqClient.variationGroup.create({ name: 'Finish', product_id: productId, is_required: true });
    createdIds.variationGroups.push(finishGroup.id);
    const optRaw = await cpqClient.variationOption.create({ name: "Raw", variation_group_id: finishGroup.id });
    const optStained = await cpqClient.variationOption.create({ name: "Stained", variation_group_id: finishGroup.id });
    variationOptions['Raw'] = optRaw.id;
    variationOptions['Stained'] = optStained.id;
    createdIds.variationOptions.push(optRaw.id, optStained.id);
    

    return { productId, variationOptions };
}


/**
 * Creates the quote configuration based on the test's financial parameters.
 * @param {object} createdIds - Object to store IDs.
 * @returns {number} - The ID of the created QuoteConfig.
 */
async function createQuoteConfig(createdIds) {
    const quoteConfig = await cpqClient.quoteConfig.create({
        name: `Test Config ${Date.now()}`,
        margin_rate: config.marginRate.toString(),
        tax_rate: config.salesTaxRate.toString(),
        sales_commission_rate: config.salesCommissionRate.toString(),
        franchise_fee_rate: config.franchiseFeeRate.toString(),
        additional_fixed_fees: '0.00',
    });
    createdIds.quoteConfigs.push(quoteConfig.id);
    return quoteConfig.id;
}

/**
 * Creates the quote, adds the product entry, and selects the variations.
 * @param {object} createdIds - Object to store IDs.
 * @param {number} productId - The ID of the product to quote.
 * @param {number} quoteConfigId - The ID of the quote config to use.
 * @param {object} variationOptions - Map of variation option names to IDs.
 * @returns {number} - The ID of the created quote.
 */
async function createAndConfigureQuote(createdIds, productId, quoteConfigId, variationOptions) {
    const quote = await cpqClient.quote.create({
        name: `Test Quote ${Date.now()}`,
        quote_config_id: quoteConfigId
    });
    createdIds.quotes.push(quote.id);

    const productEntry = await cpqClient.quoteProductEntry.create({
        quote_id: quote.id,
        product_id: productId,
        quantity_of_product_units: config.jobSize.toString(),
    });
    
    // Select variations based on the main config object
    await cpqClient.quoteProductEntryVariation.create({
        quote_product_entry_id: productEntry.id,
        variation_option_id: variationOptions['8ft']
    });
    await cpqClient.quoteProductEntryVariation.create({
        quote_product_entry_id: productEntry.id,
        variation_option_id: variationOptions[config.style]
    });
    await cpqClient.quoteProductEntryVariation.create({
        quote_product_entry_id: productEntry.id,
        variation_option_id: variationOptions[config.finish]
    });

    return quote.id;
}


/**
 * Deletes all created test data in the reverse order of creation.
 * @param {object} createdIds - An object containing arrays of IDs for each entity type.
 */
async function cleanup(createdIds) {
    // Delete in reverse order of creation to respect foreign key constraints
    const cleanupOrder = ['quotes', 'quoteConfigs', 'products', 'variationGroups', 'variationOptions', 'materials', 'unitTypes'];
    for (const modelName of cleanupOrder) {
        if(createdIds[modelName] && createdIds[modelName].length > 0) {
            console.log(`   ...deleting ${modelName}...`);
            // Use client methods that exist, e.g., product.delete, quote.delete
            // The client object has a predictable structure
            const clientMethod = modelName.endsWith('s') ? modelName.slice(0, -1) : modelName;
            
            if(cpqClient[clientMethod] && cpqClient[clientMethod].delete){
                 for (const id of createdIds[modelName].reverse()) {
                    try {
                        await cpqClient[clientMethod].delete(id);
                    } catch (err) {
                        console.warn(`   ⚠️  Could not delete ${modelName} with ID ${id}: ${err.message}`);
                    }
                }
            } else {
                 console.warn(`   ⚠️  No delete method found on client for ${clientMethod}`);
            }
        }
    }
}


module.exports = postmasterHorizontal100ftTest;
