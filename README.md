# Charlie Curtin: The Road to 500

**Red Lion edition + automatic career-win tracker.** A fan-made, mobile-friendly website for Saint Viator's girls volleyball coach. Initial count: **416 confirmed career wins as of October 28, 2026**, 84 from the goal of 500.

## What is automatic?

- **A GitHub Actions workflow runs every six hours** and reads the published [MaxPreps Saint Viator girls varsity volleyball schedule](https://www.maxpreps.com/il/arlington-heights/saint-viator-lions/volleyball/schedule/) for the current season's overall record.
- The updater converts **new season wins** into career wins, starting from the independently verified **416** total, and publishes the new `site/wins.json` to all visitors through GitHub Pages.
- The website checks `wins.json` on initial load, every five minutes while open, and whenever you return to its browser tab. You do not have to change numbers in the website.
- The logo graphic is an **original red lion-inspired illustration**, not the school's official licensed crest.

**Important limitation:** MaxPreps is a third-party public scoreboard, not an official career wins API. It can lag behind, omit tournament games, change its website, or block automated access. The source is behind the independently confirmed 416 career wins right now. This site **never estimates a new win** when a check fails; it continues to show the last confirmed total and changes the feed-status message. It is not instant live scoring. The automated fetching has been implemented and unit-tested, but cannot be verified end-to-end from this environment. Once hosted, check the first GitHub Actions run log to ensure access works.

## Publish it with GitHub Pages (one-time setup)

**GitHub is required for the automatic checks in this package.** A plain static-file host or Netlify Drop alone will **not** run the scheduled updater.

1. Sign in to [GitHub](https://github.com) and create a **public** repository, e.g. `curtin-road-to-500`. If prompted, don't initialize it with sample files, since this package already contains the files.
2. Upload the **contents** of this downloaded folder to the repository root, keeping these folder names exactly: `.github/workflows/`, `site/`, `scripts/`, `data/`, and `tests/`, plus `README.md`. Make sure the hidden `.github` folder is included. You can upload using GitHub Desktop or Git commands (below), or the GitHub website's file upload interface. Commit all files on the **main** branch.
3. Open your repository's **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. Save.
4. Open the **Actions** tab. If workflows are disabled, enable them. Select **Update wins and publish site**, then **Run workflow** if an initial run hasn't started automatically. Check it completes successfully.
5. Find your published link in **Settings → Pages**, usually `https://YOUR-USERNAME.github.io/curtin-road-to-500/`. Share this **base URL** so every visitor sees the latest available count.

This is a deploy-and-update workflow; a scheduled run will attempt to check results, save the latest published JSON, and deploy the website automatically. GitHub's scheduled actions can be delayed, especially under high load.

### Optional terminal upload method

If the GitHub web uploader makes it difficult to preserve `.github`, use GitHub Desktop or, from inside the unzipped folder:

```bash
git init -b main
git add .
git commit -m "Launch Charlie Curtin Road to 500"
git remote add origin https://github.com/YOUR-USERNAME/curtin-road-to-500.git
git push -u origin main
```

Create the empty repository in GitHub first, and replace `YOUR-USERNAME`.

## The win-count math and safeguards

The confirmed career count on October 28, 2026 is **416**. The recorded **2026-27 season baseline is 16 wins**. If the 2026 season's posted record increases to 17 wins, the counter goes to 417. If the 2027-28 season records 5 wins, another five are added. The high-water mark for each season is stored in `data/state.json` so the same season record cannot be counted twice. Earlier seasons are excluded.

The source's posted 2026 record may show fewer than the 16 baseline victories, which is why the updater never subtracts from 416. It also never counts losses, unreported matches, or a failed data fetch as a win. **If the 2026 season baseline is later found inaccurate, change it only after verifying the official career tally.**

### When a score is missing or the site is blocked

The public site retains the last confirmed career total and indicates **Scores pending** or **Feed delayed**. Check the **Actions** run log in GitHub for details. If MaxPreps changes their page format, edit `scripts/update_wins.py` to adapt the parser. This could require a developer.

### Manual verified correction (optional)

If the school confirms a total higher than MaxPreps supports, edit `data/state.json` on GitHub and increase **`verified_floor`** (e.g., to `420`). The next run will publish at least that total; the automated calculation will take over again once its source surpasses that floor. Do **not** add the missing wins to a permanent offset, or they could later be double-counted when the public source catches up.

## Files

| File | Purpose |
|---|---|
| `site/index.html` | The responsive website |
| `site/assets/red-lion.png` | Original lion-inspired red illustration |
| `site/wins.json` | Career count seen by all visitors |
| `.github/workflows/auto-update.yml` | Scheduled result check + GitHub Pages publish |
| `scripts/update_wins.py` | Public score parser and safe career-win calculation |
| `data/state.json` | Verified baseline and highest observed season records |
| `tests/test_update_wins.py` | Parser, rollover, and no-double-counting tests |

### Run local tests

```bash
python -m unittest discover -s tests -v
```

### Preview without publishing

Open `site/index.html` locally to view the design. It displays the initial 416 victories. **Automatic fetching does not operate from a local file**; it only becomes active once the GitHub repository is set up and the workflow runs.

## Source links

- [Saint Viator coach page](https://www.saintviator.com/team-detail?team=281039)
- [Public MaxPreps girls volleyball schedule](https://www.maxpreps.com/il/arlington-heights/saint-viator-lions/volleyball/schedule/)
- [Saint Viator story about Curtin's 400th win](https://www.saintviator.com/news-detail?pk=1656487)

This is an independent fan project, not an official Saint Viator High School publication or a guarantee of up-to-the-minute results.
