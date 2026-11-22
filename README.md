# NSE Scanner (hosted, shareable)
Two scans on all NSE stocks, published as a static page:
1. Never closed above listing price and currently 0-10% below it.
2. 0-10% below all-time high, optionally excluding stocks at/near a fresh ATH (ATH must be >=52 weeks old).

## Deploy (one time, ~5 minutes)
1. Create a GitHub repo and push this folder to it.
2. Settings > Pages > Deploy from branch > `main` / `/docs`.
3. Actions tab > "Scan NSE" > Run workflow. The first run builds full history (can take 1-3 hours; it
   saves progress and re-triggers itself until complete). After that it runs every weekday at 17:15 IST.
4. Share the Pages URL (https://<user>.github.io/<repo>/). Reloading shows the latest committed data.
   Use a private repo + Pages access control only if your GitHub plan supports it; Pages sites are public otherwise.

Notes: listing price = first-day open in Yahoo data; Yahoo may rate-limit GitHub runners (the job retries and resumes).
