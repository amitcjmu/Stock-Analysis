import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:8081';
const TEST_USER = {
  email: 'analyst@demo-corp.com',
  password: 'Demo123!'
};

test.describe('Debug Upload Process', () => {
  test('Debug CMDB upload step by step', async ({ page }) => {
    test.setTimeout(180000);
    
    // Login
    console.log('🔐 Logging in...');
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Go to CMDB import
    console.log('📁 Going to CMDB import...');
    await page.goto(`${BASE_URL}/discovery/cmdb-import`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Screenshot 1: Initial state
    await page.screenshot({ path: 'test-results/01-cmdb-import-initial.png', fullPage: true });
    
    // Check for blocked state
    const blockedText = await page.locator('text=/upload blocked|data upload disabled/i').all();
    console.log(`Blocked indicators: ${blockedText.length}`);
    
    if (blockedText.length > 0) {
      console.log('⚠️ Upload is blocked');
      
      // Look for delete button
      const deleteBtn = page.locator('button:has-text("Delete")');
      if (await deleteBtn.isVisible()) {
        console.log('🗑️ Clicking delete button...');
        await deleteBtn.click();
        await page.waitForTimeout(2000);
        
        // Confirm if needed
        const confirmBtn = page.locator('button:has-text("Confirm"), button:has-text("Yes")');
        if (await confirmBtn.isVisible()) {
          await confirmBtn.click();
          await page.waitForTimeout(2000);
        }
        
        // Reload page
        await page.reload();
        await page.waitForTimeout(3000);
        
        // Screenshot 2: After delete
        await page.screenshot({ path: 'test-results/02-after-delete.png', fullPage: true });
      }
    }
    
    // Now look for all possible upload elements
    console.log('\n🔍 Looking for upload elements...');
    
    const uploadSelectors = [
      'input[type="file"]',
      '.upload-area',
      '.upload-zone',
      '.dropzone',
      '.border-dashed',
      '[data-testid*="upload"]',
      'button:has-text("Upload")',
      'button:has-text("Select")',
      'button:has-text("Choose")',
      'div[role="button"]',
      '[class*="upload"]',
      '[class*="drop"]'
    ];
    
    for (const selector of uploadSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        console.log(`✅ Found ${count} elements matching: ${selector}`);
        
        // Get more details about first element
        const firstElement = page.locator(selector).first();
        const isVisible = await firstElement.isVisible();
        const tagName = await firstElement.evaluate(el => el.tagName);
        const className = await firstElement.evaluate(el => el.className);
        
        console.log(`   Tag: ${tagName}, Visible: ${isVisible}, Class: ${className}`);
      }
    }
    
    // Look for any divs with upload-related text
    const uploadDivs = await page.locator('div:has-text("upload"), div:has-text("drop"), div:has-text("CMDB")').all();
    console.log(`\nFound ${uploadDivs.length} divs with upload-related text`);
    
    for (let i = 0; i < Math.min(uploadDivs.length, 5); i++) {
      const div = uploadDivs[i];
      const text = await div.textContent();
      console.log(`Div ${i}: ${text?.substring(0, 100)}...`);
    }
    
    // Try to find the upload area by looking for the CMDB Export Data card
    console.log('\n🎯 Looking for CMDB Export Data card...');
    const cmdbCard = page.locator('text="CMDB Export Data"').first();
    if (await cmdbCard.isVisible()) {
      console.log('✅ Found CMDB Export Data card');
      
      // Look for upload button within the card's parent
      const cardParent = cmdbCard.locator('..');
      const uploadInCard = cardParent.locator('button, [role="button"], .cursor-pointer').all();
      console.log(`Found ${(await uploadInCard).length} clickable elements in card`);
      
      // Try clicking the first one
      if ((await uploadInCard).length > 0) {
        console.log('🖱️ Clicking first clickable element in card...');
        await (await uploadInCard)[0].click();
        await page.waitForTimeout(2000);
        
        // Screenshot 3: After click
        await page.screenshot({ path: 'test-results/03-after-card-click.png', fullPage: true });
        
        // Check for file input again
        const fileInputAfterClick = await page.locator('input[type="file"]').count();
        console.log(`File inputs after click: ${fileInputAfterClick}`);
      }
    }
    
    // Final check for any file inputs
    const finalFileInputs = await page.locator('input[type="file"]').all();
    console.log(`\n📊 Final file input count: ${finalFileInputs.length}`);
    
    if (finalFileInputs.length > 0) {
      console.log('🎉 File input found! Attempting upload...');
      const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
      await finalFileInputs[0].setInputFiles(testFilePath);
      await page.waitForTimeout(5000);
      
      // Screenshot 4: After upload
      await page.screenshot({ path: 'test-results/04-after-upload.png', fullPage: true });
    } else {
      console.log('❌ No file inputs found - upload mechanism unclear');
    }
    
    // Final screenshot
    await page.screenshot({ path: 'test-results/05-final-state.png', fullPage: true });
  });
});