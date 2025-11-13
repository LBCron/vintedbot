#!/usr/bin/env python3
import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

from backend.utils.logger import logger
from backend.utils.crypto import decrypt_blob
from backend.db import get_publish_job, update_job_status, get_session
from backend.models import JobStatus

HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

CAPTCHA_SELECTORS = [
    "[data-testid='captcha']",
    "#captcha",
    ".captcha-container",
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']"
]


async def run_playwright_job(job_id: str, headless: bool = True):
    """Execute a Playwright automation job"""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install")
        update_job_status(job_id, JobStatus.failed, logs=[
            {"timestamp": datetime.utcnow().isoformat(), "message": "Playwright not installed"}
        ])
        return
    
    job = get_publish_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return
    
    if not job.session_id:
        logger.error(f"Job {job_id} has no session_id")
        update_job_status(job_id, JobStatus.failed, logs=[
            {"timestamp": datetime.utcnow().isoformat(), "message": "No session_id provided"}
        ])
        return
    
    # Get and decrypt session cookie
    session = get_session(job.session_id)
    if not session:
        logger.error(f"Session {job.session_id} not found")
        update_job_status(job_id, JobStatus.failed, logs=[
            {"timestamp": datetime.utcnow().isoformat(), "message": "Session not found"}
        ])
        return
    
    try:
        cookie_value = decrypt_blob(session.encrypted_cookie)
    except Exception as e:
        logger.error(f"Failed to decrypt cookie: {e}")
        update_job_status(job_id, JobStatus.failed, logs=[
            {"timestamp": datetime.utcnow().isoformat(), "message": "Failed to decrypt cookie"}
        ])
        return
    
    # Start job
    logs = []
    update_job_status(job_id, JobStatus.running, logs=logs)
    
    async with async_playwright() as p:
        # Get Chromium path from Nix (fix for Replit NixOS)
        import subprocess
        try:
            chromium_path = subprocess.check_output(['which', 'chromium']).decode().strip()
            browser = await p.chromium.launch(
                executable_path=chromium_path,
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
        except:
            # Fallback to Playwright's bundled browser
            browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        
        # Add cookie to context
        try:
            await context.add_cookies([{
                "name": "_vinted_fr_session",
                "value": cookie_value,
                "domain": ".vinted.com",
                "path": "/"
            }])
            logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Cookie loaded into browser context"
            })
        except Exception as e:
            logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Failed to add cookie: {e}"
            })
            await browser.close()
            update_job_status(job_id, JobStatus.failed, logs=logs)
            return
        
        page = await context.new_page()
        
        try:
            # Navigate to Vinted
            await page.goto("https://www.vinted.com", wait_until="networkidle")
            logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Navigated to Vinted homepage"
            })
            
            # Check for CAPTCHA
            captcha_found = False
            for selector in CAPTCHA_SELECTORS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        captcha_found = True
                        break
                except:
                    pass
            
            if captcha_found:
                screenshot_path = f"backend/data/screenshots/{job_id}_captcha.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await page.screenshot(path=screenshot_path)
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "⚠️ CAPTCHA detected - automation blocked",
                    "level": "warning"
                })
                update_job_status(job_id, JobStatus.blocked, logs=logs, screenshot_path=screenshot_path)
                
                # Send Telegram notification
                try:
                    from backend.monitoring.telegram_notifier import TelegramNotifier
                    notifier = TelegramNotifier()
                    caption = f"🚨 CAPTCHA Detected!\n\nJob ID: {job_id}\nStatus: Blocked\n\nManual intervention may be required to continue."
                    await asyncio.to_thread(notifier.send_photo, photo_path=screenshot_path, caption=caption)
                except Exception as e:
                    logger.error(f"Failed to send Telegram notification for CAPTCHA: {e}")

                await browser.close()
                logger.warning(f"Job {job_id} blocked by CAPTCHA")
                return
            
            # Get listing details for the job
            from backend.db import get_listing
            listing = get_listing(job.item_id)
            if not listing:
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Listing with ID {job.item_id} not found for job {job_id}",
                    "level": "error"
                })
                update_job_status(job_id, JobStatus.failed, logs=logs)
                await browser.close()
                return

            # Continue with automation based on job mode
            if job.mode == "manual":
                # For manual mode, navigate to the form but don't submit
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Manual mode: Ready for user to complete"
                })
                screenshot_path = f"backend/data/screenshots/{job_id}_preview.png"
                await page.screenshot(path=screenshot_path)
                update_job_status(job_id, JobStatus.completed, logs=logs, screenshot_path=screenshot_path)
            
            elif job.mode == "automated":
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Automated mode: Starting publish action"
                })

                # 1. Navigate to upload page
                await page.goto("https://www.vinted.com/items/new", wait_until="networkidle")
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "Navigated to items/new"})

                # 2. Upload photos
                # Vinted's upload is a complex dropzone. We target the hidden input element.
                photo_paths = [os.path.abspath(p) for p in listing.photos]
                await page.set_input_files("input[type='file']", photo_paths)
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": f"Uploading {len(listing.photos)} photos"})
                
                # Wait for all photos to be uploaded and processed by Vinted
                await page.wait_for_selector(".media-item-list.is-clickable", timeout=60000) # Wait up to 60s
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "Photos appear to be uploaded"})

                # 3. Fill text fields
                await page.fill("input[name='title']", listing.title)
                await page.fill("textarea[name='description']", listing.description)
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "Filled title and description"})

                # 4. Select Category
                if listing.category:
                    logs.append({"timestamp": datetime.utcnow().isoformat(), "message": f"Selecting category: {listing.category}"})
                    await page.click("div[data-testid='catalog-tree-select-button']")
                    
                    # Wait for the category modal to appear
                    await page.wait_for_selector("div[data-testid='catalog-tree-modal-content']", timeout=5000)

                    category_parts = [part.strip() for part in listing.category.split('/')]
                    for part in category_parts:
                        # Click on the element containing the category part text
                        await page.locator('div[data-testid*="catalog-tree-item"] >> text='{}''.format(part)).click()
                        # Small delay to allow UI to update
                        await page.wait_for_timeout(500)
                    
                    logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "Dynamic category selected"})
                else:
                    logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "No category provided, skipping selection.", "level": "warning"})


                # 5. Fill Brand
                if listing.brand:
                    await page.fill("input[placeholder='Marque']", listing.brand)
                    # Wait for the dropdown and click the first result
                    await page.locator(".is-suggestion").first.click()
                    logs.append({"timestamp": datetime.utcnow().isoformat(), "message": f"Filled brand: {listing.brand}"})

                # 6. Fill Price
                await page.fill("input[name='price']", str(listing.price))
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": f"Filled price: {listing.price}"})

                # 7. Submit
                await page.click("button[type='submit']")
                logs.append({"timestamp": datetime.utcnow().isoformat(), "message": "Clicked submit button"})

                # 8. Verify
                # Wait for either a success message or a redirect to the new item page
                await page.wait_for_url("**/items/**", timeout=60000)
                
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"✅ Automated publish completed. New URL: {page.url}"
                })
                update_job_status(job_id, JobStatus.completed, logs=logs)
            
            logger.info(f"✅ Job {job_id} completed successfully")
        
        except Exception as e:
            screenshot_path = f"backend/data/screenshots/{job_id}_error.png"
            await page.screenshot(path=screenshot_path)
            logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Error: {str(e)}",
                "level": "error"
            })
            update_job_status(job_id, JobStatus.failed, logs=logs, screenshot_path=screenshot_path)
            logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            await browser.close()


async def worker_loop():
    """Main worker loop - polls for jobs and executes them"""
    logger.info("🤖 Playwright worker started")
    
    while True:
        try:
            from sqlmodel import select
            from backend.db import get_db_session
            from backend.models import PublishJob
            
            # Check for queued jobs
            with get_db_session() as db:
                job = db.exec(
                    select(PublishJob)
                    .where(PublishJob.status == JobStatus.queued)
                    .order_by(PublishJob.created_at)
                ).first()
                
                if job:
                    logger.info(f"📋 Processing job {job.job_id}")
                    await run_playwright_job(job.job_id, headless=HEADLESS)
            
            # Sleep before next check
            await asyncio.sleep(5)
        
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Playwright Worker")
    parser.add_argument("--headless", type=int, default=1, help="Run in headless mode (1=yes, 0=no)")
    args = parser.parse_args()
    
    headless_mode = bool(args.headless)
    HEADLESS = headless_mode
    
    logger.info(f"Starting Playwright worker (headless={headless_mode})")
    asyncio.run(worker_loop())
