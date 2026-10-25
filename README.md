# Dream Inventory

A Valorant inventory builder. Pick a skin for every weapon and see the total cost in VP, USD and TND.

The site is the `docs/` folder. A workflow refreshes the skin list and pictures every day, so new skins show up on their own.

## Put it online (GitHub Pages, free)

1. Make a free account at github.com and create a new **public** repository.
2. Upload everything from this folder: `docs/`, `.github/`, `update_site.py` and this README. On the repository page choose **Add file > Upload files** and drag the folders in. Commit.
3. Open **Settings > Pages**. Under "Build and deployment" choose **Deploy from a branch**, branch **main**, folder **/docs**, then Save. After a minute your site is live at `https://YOUR-NAME.github.io/REPOSITORY-NAME/`.
4. Open the **Actions** tab. If GitHub asks, enable workflows. Pick **Update skins** and press **Run workflow** once. This pulls today's skins and checks that the daily update works. After that it runs every day by itself.

If the workflow fails with a permissions error, go to **Settings > Actions > General > Workflow permissions** and choose **Read and write permissions**.

## What is in here

- `docs/index.html`: the website.
- `docs/catalog.json` and `docs/atlas/`: the skin list and the small pictures. The starting copy was made from the zip you sent. The daily workflow replaces it with fresh data.
- `update_site.py`: downloads every skin and rebuilds the pictures. You can run it yourself with `pip install pillow` and `python update_site.py`.
- `.github/workflows/update.yml`: runs the script every day and saves the result.

## Notes

- Prices come from the standard store tiers and are set inside `docs/index.html`. If Riot changes them, edit the numbers near the top of the script section.
- If Riot's API is down on a given day, the script keeps the old data instead of replacing it with a broken copy.
- Skin pictures belong to Riot Games. This is a fan-made tool.
