// Test runner for E2E tests
const fs = require('fs');
const path = require('path');

// Import all test files
const unitTypeCrudTest = require('./tests/unit-type-crud-test');
const productCrudTest = require('./tests/product-crud-test'); // Add this line
const postmasterHorizontal100ftTest = require('./tests/postmaster-h')
async function runAllTests() {
    console.log('🚀 Starting E2E Test Suite...\n');
    
    let passedTests = 0;
    let failedTests = 0;
    const results = [];

    const tests = [
        { name: 'Unit Type CRUD Test', testFunction: unitTypeCrudTest },
        { name: 'Product CRUD Test', testFunction: productCrudTest },
        { name: 'Postmaster Horizontal 100ft Test', testFunction: postmasterHorizontal100ftTest },
    ];

    for (const test of tests) {
        try {
            console.log(`📋 Running: ${test.name}`);
            await test.testFunction();
            console.log(`✅ PASSED: ${test.name}\n`);
            passedTests++;
            results.push({ name: test.name, status: 'PASSED' });
        } catch (error) {
            console.error(`❌ FAILED: ${test.name}`);
            console.error(`   Error: ${error.message}\n`);
            // traceback for debugging
            if (error.stack) {
                console.error(`   Stack Trace: ${error.stack}\n`);
            }
            failedTests++;
            results.push({ name: test.name, status: 'FAILED', error: error.message });
        }
    }

    // Print summary
    console.log('📊 Test Summary:');
    console.log(`   Total: ${tests.length}`);
    console.log(`   Passed: ${passedTests}`);
    console.log(`   Failed: ${failedTests}`);
    
    if (failedTests > 0) {
        console.log('\n❌ Failed Tests:');
        results.filter(r => r.status === 'FAILED').forEach(r => {
            console.log(`   - ${r.name}: ${r.error}`);
        });
        process.exit(1);
    } else {
        console.log('\n🎉 All tests passed!');
        process.exit(0);
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    runAllTests().catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
}

module.exports = { runAllTests };
